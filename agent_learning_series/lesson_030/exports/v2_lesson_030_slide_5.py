import tiktoken

class TokenAwarePruner:
    def __init__(self, model_name: str = "gpt-4", max_allowed_tokens: int = 2048):
        self.encoder = tiktoken.encoding_for_model(model_name)
        self.max_tokens = max_allowed_tokens

    def prune_context(self, short_term_buffer: List[Dict[str, str]], query: str) -> List[Dict[str, str]]:
        current_payload = list(short_term_buffer)
        while len(current_payload) > 0:
            # Calculate cumulative token count
            raw_text = query + " ".join([f"{m['user']} {m['system']}" for m in current_payload])
            tokens = len(self.encoder.encode(raw_text))
            if tokens <= self.max_tokens:
                return current_payload
            # Evict oldest conversation pair
            current_payload.pop(0)
        return []