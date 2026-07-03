class RecursiveTextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> list[str]:
        # High-performance simulation of recursive separation
        chunks = []
        for sep in self.separators:
            splits = text.split(sep) if sep else list(text)
            current_chunk = ""
            
            for split in splits:
                if len(current_chunk) + len(split) < self.chunk_size:
                    current_chunk += (sep if current_chunk else "") + split
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = split
            if current_chunk:
                chunks.append(current_chunk)
            
            # If any chunk still exceeds size, continue recursion
            if all(len(c) <= self.chunk_size for c in chunks):
                break
        return chunks

# Instantiate the class with standard engineering values
splitter = RecursiveTextSplitter(chunk_size=120, chunk_overlap=10)
sample_text = "Recursive splitters are powerful.\n\nThey preserve paragraphs perfectly.\nThey fallback gracefully to spaces."
print(splitter.split_text(sample_text))