"""
Chat agent module for conversational interaction with RAG (Retrieval-Augmented Generation).
Integrates Claude API with document retrieval to provide grounded, actionable guidance.
"""
from typing import List, Dict, Any, Optional
from anthropic import Anthropic


class ChatAgent:
    """Conversational agent with document-grounded responses."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929",
                 max_tokens: int = 4096, temperature: float = 0.7):
        """
        Initialize chat agent.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # System prompt for operational decision support
        self.system_prompt = """You are Notev, an AI-powered assistant designed to support Operations Centers in real-time decision-making.

Your role is to:
1. Analyze operational situations based on provided documents and context
2. Synthesize information into clear, actionable guidance
3. Help operators assess scenarios, consider options, and respond effectively
4. Identify risks, constraints, and critical considerations
5. Provide both document-based information AND general best practices/suggestions

CRITICAL GUIDELINES:
- ALWAYS clearly distinguish between information from documents and general suggestions
- When citing document information, use phrases like: "According to [document name]..." or "The documents state..."
- When providing general suggestions or best practices, use phrases like: "Based on general best practices..." or "I suggest considering..." or "A common approach is..."
- If documents provide relevant information, prioritize that FIRST, then add general suggestions if helpful
- When documents conflict, identify the conflict clearly and ask for user clarification
- Structure responses to be action-oriented and operationally relevant
- Use clear, professional language suitable for high-stakes decision-making

Response Structure:
1. First, summarize what the documents say (if relevant)
2. Then, identify any gaps in the documented information
3. Finally, provide general suggestions or best practices to supplement the documented procedures

When analyzing situations:
- Consider available resources and procedures from the documents
- Identify potential risks and mitigation strategies from both documents and general knowledge
- Suggest next steps or decision points
- Note any time-sensitive considerations
- Flag uncertainty or gaps in information
- Offer additional suggestions based on common operational practices when appropriate

Remember: You are advisory only. Operators make the final decisions. Always be transparent about the source of your information."""

    def generate_response(self, user_message: str, conversation_history: List[Dict[str, str]],
                         retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a response using Claude with RAG.

        Args:
            user_message: Current user message
            conversation_history: Previous conversation turns (list of {role, content} dicts)
            retrieved_docs: Retrieved document chunks from vector search

        Returns:
            Dictionary containing response and metadata
        """
        # Build context from retrieved documents
        context = self._build_document_context(retrieved_docs)

        # Build messages list
        messages = []

        # Add conversation history
        for turn in conversation_history:
            messages.append({
                'role': turn['role'],
                'content': turn['content']
            })

        # Add current message with context
        if context:
            current_message = f"""RETRIEVED DOCUMENTS:
{context}

USER QUESTION:
{user_message}

Please provide guidance based on the above documents and conversation context."""
        else:
            current_message = user_message

        messages.append({
            'role': 'user',
            'content': current_message
        })

        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=messages
            )

            response_text = response.content[0].text

            return {
                'response': response_text,
                'model': self.model,
                'retrieved_docs_count': len(retrieved_docs),
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }

        except Exception as e:
            return {
                'error': str(e),
                'response': f"I encountered an error while processing your request: {str(e)}"
            }

    def _build_document_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved documents.

        Args:
            retrieved_docs: List of retrieved document chunks

        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return ""

        context_parts = []

        for i, doc in enumerate(retrieved_docs, 1):
            doc_id = doc.get('doc_id', 'unknown')
            filename = doc.get('metadata', {}).get('filename', 'unknown')
            text = doc.get('text', '')
            score = doc.get('similarity_score', 0)

            context_parts.append(f"""--- Document {i} (Relevance: {score:.2f}) ---
Source: {filename} [ID: {doc_id}]
Content:
{text}
""")

        return "\n".join(context_parts)

    def check_for_conflicts(self, retrieved_docs: List[Dict[str, Any]]) -> Optional[str]:
        """
        Use Claude to identify potential conflicts in retrieved documents.

        Args:
            retrieved_docs: Retrieved document chunks

        Returns:
            Conflict analysis or None if no significant conflicts detected
        """
        if len(retrieved_docs) < 2:
            return None

        context = self._build_document_context(retrieved_docs)

        conflict_check_prompt = f"""Review the following documents and identify any contradictions or conflicts in the information they contain.

{context}

If you find conflicts, describe them clearly. If no significant conflicts exist, respond with "NO CONFLICTS DETECTED"."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                system="You are analyzing documents for conflicts and contradictions.",
                messages=[{
                    'role': 'user',
                    'content': conflict_check_prompt
                }]
            )

            analysis = response.content[0].text

            if "NO CONFLICTS DETECTED" in analysis.upper():
                return None

            return analysis

        except Exception as e:
            print(f"Error checking for conflicts: {e}")
            return None

    def summarize_documents(self, doc_texts: List[str], purpose: str = "general") -> str:
        """
        Generate a summary of multiple documents.

        Args:
            doc_texts: List of document texts to summarize
            purpose: Purpose of the summary (e.g., "general", "procedures", "resources")

        Returns:
            Summary text
        """
        if not doc_texts:
            return "No documents to summarize."

        combined_text = "\n\n---\n\n".join(doc_texts)

        summary_prompt = f"""Summarize the following documents for {purpose} operational purposes. Focus on key information, procedures, resources, and constraints.

DOCUMENTS:
{combined_text}

Provide a concise but comprehensive summary."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.5,
                system="You are summarizing operational documents for decision support.",
                messages=[{
                    'role': 'user',
                    'content': summary_prompt
                }]
            )

            return response.content[0].text

        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def extract_action_items(self, conversation_history: List[Dict[str, str]]) -> List[str]:
        """
        Extract action items from conversation history.

        Args:
            conversation_history: List of conversation turns

        Returns:
            List of action items
        """
        if not conversation_history:
            return []

        conversation_text = "\n".join([
            f"{turn['role'].upper()}: {turn['content']}"
            for turn in conversation_history
        ])

        prompt = f"""Review this operational conversation and extract clear action items or recommendations that were discussed.

CONVERSATION:
{conversation_text}

List only specific, actionable items. If none exist, respond with "NO ACTION ITEMS"."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                system="You are extracting action items from operational conversations.",
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )

            result = response.content[0].text

            if "NO ACTION ITEMS" in result.upper():
                return []

            # Parse action items (assume they're in a list or numbered format)
            lines = result.strip().split('\n')
            action_items = [
                line.strip('- ').strip('0123456789. ').strip()
                for line in lines
                if line.strip() and not line.strip().startswith('#')
            ]

            return action_items

        except Exception as e:
            print(f"Error extracting action items: {e}")
            return []
