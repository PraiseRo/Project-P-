import asyncio
from typing import Optional, Dict, Any
from app.core.events import AssistantState, event_bus
from app.core.logging_config import setup_logger
from app.core.conversation import ConversationManager
from app.core.routines import routine_manager
from app.ai.provider import AIProvider, SYSTEM_PROMPT
from app.ai.hybrid_router import LocalIntentRouter
from app.voice.speech_to_text import SpeechToTextProvider
from app.voice.text_to_speech import TextToSpeechProvider
from app.voice.microphone import MicrophoneManager
from app.voice.hotkey import PushToTalkListener
from app.tools.registry import tool_registry
from app.security.policies import SecurityPolicy

logger = setup_logger("assistant.orchestrator")

class AssistantOrchestrator:
    """Master orchestrator with Hybrid (Offline PC Control + Online Web Intelligence) Routing."""

    def __init__(
        self,
        ai_provider: AIProvider,
        stt_provider: SpeechToTextProvider,
        tts_provider: TextToSpeechProvider,
        microphone_manager: Optional[MicrophoneManager] = None,
        security_policy: Optional[SecurityPolicy] = None,
        async_loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        self.ai = ai_provider
        self.stt = stt_provider
        self.tts = tts_provider
        self.mic = microphone_manager or MicrophoneManager()
        self.security = security_policy or SecurityPolicy()
        self.conversation = ConversationManager(system_prompt=SYSTEM_PROMPT)
        self.state = AssistantState.IDLE
        self._emergency_stop_requested = False
        self.async_loop = async_loop

        self.hotkey_listener = PushToTalkListener(
            on_press_callback=self._on_push_to_talk_pressed,
            on_release_callback=self._on_push_to_talk_released,
            on_emergency_stop=self.trigger_emergency_stop
        )

    def set_state(self, new_state: AssistantState):
        self.state = new_state
        logger.info(f"State transitioned to: {new_state.value}")
        event_bus.publish("state_change", new_state)

    def trigger_emergency_stop(self):
        """Immediately aborts running tasks and silences speech."""
        logger.warning("Triggering EMERGENCY STOP across all subsystems!")
        self._emergency_stop_requested = True
        self.set_state(AssistantState.IDLE)
        event_bus.publish("emergency_stop", True)

    def _on_push_to_talk_pressed(self):
        if self.state == AssistantState.IDLE:
            self._emergency_stop_requested = False
            self.set_state(AssistantState.LISTENING)
            self.mic.start_recording()

    def _on_push_to_talk_released(self):
        if self.state == AssistantState.LISTENING:
            audio_bytes = self.mic.stop_recording()
            if self.async_loop and self.async_loop.is_running():
                asyncio.run_coroutine_threadsafe(self.process_audio_command(audio_bytes), self.async_loop)
            else:
                try:
                    asyncio.create_task(self.process_audio_command(audio_bytes))
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self.process_audio_command(audio_bytes))

    async def process_audio_command(self, audio_bytes: bytes):
        """Pipeline: Transcribe Audio -> Hybrid Intent / AI -> Execution -> TTS."""
        if not audio_bytes or self._emergency_stop_requested:
            self.set_state(AssistantState.IDLE)
            return

        try:
            self.set_state(AssistantState.THINKING)
            # Step 1: Transcribe user speech
            user_text = await self.stt.transcribe(audio_bytes)
            if not user_text:
                self.set_state(AssistantState.IDLE)
                return

            logger.info(f"User Command: '{user_text}'")
            event_bus.publish("user_message", user_text)
            
            # Step 2: Run through hybrid processor
            await self.process_text_command(user_text)

        except Exception as e:
            logger.error(f"Error processing audio command: {e}", exc_info=True)
            self.set_state(AssistantState.ERROR)
            await self.tts.speak("Sorry, I encountered an error.")
            self.set_state(AssistantState.IDLE)

    async def process_text_command(self, user_text: str):
        """Processes a text command via Fast Offline Local Routing, Custom Routines, or Online LLM."""
        self.set_state(AssistantState.THINKING)
        self.conversation.add_user_message(user_text)

        # 1. FAST LOCAL OFFLINE ROUTING & ROUTINES
        local_match = LocalIntentRouter.match_local_command(user_text)
        if local_match:
            tool_name, args, spoken_preamble = local_match
            self.set_state(AssistantState.EXECUTING)

            if tool_name == "execute_routine":
                logger.info("Executing custom multi-step routine...")
                resp_text = await routine_manager.execute_routine(args["routine"])
            else:
                logger.info(f"Fast Local Offline Execution: {tool_name} with {args}")
                try:
                    result = await tool_registry.execute(tool_name, args)
                    resp_text = result.get("message", spoken_preamble)
                except Exception as err:
                    resp_text = f"Failed to execute {tool_name}: {str(err)}"

            if not self._emergency_stop_requested:
                self.set_state(AssistantState.SPEAKING)
                event_bus.publish("assistant_message", resp_text)
                await self.tts.speak(resp_text)

            self.set_state(AssistantState.IDLE)
            return

        # 2. ONLINE / LLM REASONING & GENERAL CHAT
        tools = tool_registry.to_openai_tools()
        try:
            response = await self.ai.chat(messages=self.conversation.get_messages(), tools=tools)
        except Exception as e:
            logger.error(f"AI Provider error (may be offline): {e}")
            resp_text = "I couldn't reach the online AI service. You can still use local PC commands or routines like 'setup my workspace'."
            self.set_state(AssistantState.SPEAKING)
            event_bus.publish("assistant_message", resp_text)
            await self.tts.speak(resp_text)
            self.set_state(AssistantState.IDLE)
            return

        if self._emergency_stop_requested:
            self.set_state(AssistantState.IDLE)
            return

        # Check for tool execution
        tool_calls = response.get("tool_calls", [])
        if tool_calls:
            self.set_state(AssistantState.EXECUTING)
            for tc in tool_calls:
                if self._emergency_stop_requested:
                    break

                tool_name = tc.get("name")
                args = tc.get("arguments", {})
                call_id = tc.get("id", "call_1")

                tool_def = tool_registry.get_tool(tool_name)
                risk_level = tool_def.risk_level if tool_def else 0

                # Security check
                if self.security.requires_confirmation(tool_name, risk_level):
                    logger.warning(f"Tool {tool_name} requires confirmation.")
                    result = {"status": "cancelled", "message": f"Action {tool_name} requires explicit user confirmation."}
                else:
                    try:
                        result = await tool_registry.execute(tool_name, args)
                    except Exception as err:
                        result = {"status": "error", "message": str(err)}

                self.conversation.add_tool_result(tool_call_id=call_id, name=tool_name, result=result)

            # Get final conversational summary from AI after tool results
            final_resp = await self.ai.chat(messages=self.conversation.get_messages(), tools=None)
            content = final_resp.get("content", "Done.")
        else:
            content = response.get("content", "")

        # Step 3: Speak response
        if content and not self._emergency_stop_requested:
            self.set_state(AssistantState.SPEAKING)
            event_bus.publish("assistant_message", content)
            await self.tts.speak(content)

        self.set_state(AssistantState.IDLE)
