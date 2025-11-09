"""LLM-powered agent for intelligent web automation"""
from typing import Dict, Any, List
import json
import base64
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .config import OPENAI_API_KEY
from .prompts import (
    SYSTEM_PROMPT,
    QUERY_PARSER_PROMPT,
    ACTION_DECISION_PROMPT,
    INITIAL_NAVIGATION_PROMPT,
)


class LLMAgent:
    """LLM-powered agent for decision making using GPT-4 Vision"""

    def __init__(self, model: str = "gpt-4o"):
        """Initialize LLM agent with GPT-4"""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=OPENAI_API_KEY,
            max_tokens=1024,
            temperature=0.7,
        )
        self.action_history: List[Dict] = []

    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse user query to extract app and task"""
        print(f"\nParsing query: {query}")

        prompt = QUERY_PARSER_PROMPT.format(query=query)

        messages = [
            SystemMessage(content="You are a query parser. Respond only with valid JSON."),
            HumanMessage(content=prompt),
        ]

        response = self.llm.invoke(messages)

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            parsed = json.loads(content)
            print(f"Parsed: app={parsed['app']}, task={parsed['task']}")
            return parsed
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response: {e}")
            print(f"Response was: {response.content}")
            return {
                "app": "unknown",
                "task": query,
                "keywords": query.split()
            }

    def decide_action(
        self,
        task: str,
        screenshot_path: Path,
        state_info: Dict[str, Any],
        is_initial: bool = False
    ) -> Dict[str, Any]:
        """Decide next action based on screenshot and state"""
        print(f"\nDeciding next action for: {task}")

        with open(screenshot_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        history_str = "\n".join([
            f"- {i+1}. {action['action']}: {action.get('description', 'N/A')}"
            for i, action in enumerate(self.action_history[-5:])
        ]) or "None yet (this is the first action)"

        if is_initial:
            prompt = INITIAL_NAVIGATION_PROMPT.format(
                task=task,
                app=state_info.get('app', 'unknown'),
                url=state_info.get('url', 'unknown'),
            )
        else:
            prompt = ACTION_DECISION_PROMPT.format(
                task=task,
                url=state_info.get('url', 'unknown'),
                title=state_info.get('title', 'unknown'),
                action_history=history_str,
                has_modal=state_info.get('has_modal', False),
                has_dropdown=state_info.get('has_dropdown', False),
                element_count=state_info.get('element_count', 0),
            )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_data}",
                        "detail": "high"
                    },
                },
            ]),
        ]

        response = self.llm.invoke(messages)

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            action = json.loads(content)

            print(f"Decision: {action['action']}")
            print(f"   Reasoning: {action.get('reasoning', 'N/A')[:100]}...")

            self.action_history.append(action)

            return action

        except json.JSONDecodeError as e:
            print(f"Failed to parse action: {e}")
            print(f"Response was: {response.content}")

            return {
                "action": "wait",
                "milliseconds": 2000,
                "description": "Failed to parse LLM response",
                "reasoning": "Error in LLM output, waiting to retry"
            }

    def reset_history(self):
        """Clear action history"""
        self.action_history = []
        print("Action history cleared")
