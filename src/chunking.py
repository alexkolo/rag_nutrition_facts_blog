import re


def recursive_text_splitter(text: str, n_char_max: int = 1000, overlap: int = 100) -> list[str]:
    """
    Helper function for chunking text recursively.

    Copy from https://github.com/lancedb/vectordb-recipes/blob/main/tutorials/RAG-from-Scratch/RAG_from_Scratch.ipynb

    This function splits a long text into smaller chunks based on a specified
    maximum chunk length (`n_char_max`) and an overlap size (`overlap`).
    It aims to maintain logical continuity by avoiding breaking sentences or
    paragraphs at inappropriate places.

    Parameters
    ----------
    text : str
        The input text to be split into chunks.
    n_char_max : int, optional
        The maximum number of characters of each chunk. Default is 1000 (~250 tokens).
    overlap : int, optional
        The number of characters to overlap between chunks. Default is 100 (~25 tokens).

    Returns
    -------
    list[str]
        A list of text chunks, each no longer than `n_char_max`.
    """

    # Initialize result list to store the chunks
    result: list[str] = []

    # Initialize the current chunk count to track position in the text
    current_chunk_count: int = 0

    # list of separators to use for splitting the text
    separator: list[str] = ["\n", " "]  # ["\n\n", "\n", " ", ""]

    # Split the text using the separators
    _splits: list[str] = re.split(f"({separator})", text)

    # Reconstruct segments into pairs, combining each separator with the text following it
    splits: list[str] = [_splits[i] + _splits[i + 1] for i in range(1, len(_splits), 2)]

    # Loop through the splits to create chunks
    for i in range(len(splits)):
        if current_chunk_count != 0:
            # Create a chunk with overlap from the previous chunk
            chunk: str = "".join(splits[current_chunk_count - overlap : current_chunk_count + n_char_max])
        else:
            # Create the first chunk without any overlap
            chunk: str = "".join(splits[0:n_char_max])

        # If the chunk is not empty, append it to the result list
        if len(chunk) > 0:
            result.append("".join(chunk))

        # Increment the chunk count to move to the next position
        current_chunk_count += n_char_max

    # Return the list of text chunks
    return result


def text_has_only_questions(text: str) -> bool:
    """
    Returns True if the input string contains question marks but not periods or exclamation marks.
    (aka text consists of only questions but no information)
    """
    return "?" in text and "." not in text and "!" not in text


def split_and_filter_paragraphs(paragraphs: list[str], n_char_max: int = 1000, overlap: int = 100) -> list[str]:
    """
    Processes a list of paragraphs, splitting any paragraph that exceeds the maximum token limit.
    Ignores paragraphs that contain only questions.

    Parameters
    ----------
    paragraphs : list[str]
        A list of paragraphs to be processed.
    n_char_max : int, optional
        The maximum number of characters of each chunk. Default is 1000 (~250 tokens).
    overlap : int, optional
        The number of characters to overlap between chunks. Default is 100 (~25 tokens).

    Returns
    -------
    list[str]
        A list of processed paragraphs with long paragraphs split into smaller chunks.
    """
    paragraphs_new: list[str] = []
    for para in paragraphs:
        if text_has_only_questions(para):
            continue
        if len(para) > n_char_max:
            para_chunks: list[str] = recursive_text_splitter(para, n_char_max, overlap)
            paragraphs_new.extend(para_chunks)
        else:
            paragraphs_new.append(para)

    return paragraphs_new
