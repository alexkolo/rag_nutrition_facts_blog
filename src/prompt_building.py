import re

BOT_INSTRUCTION: str = """
<instruction>
You are a digital assistant drawing from over 1,200 blog posts written by Dr. Greger and his team on topics related to healthy eating and living, all stored in your knowledge base.

Your goal is to provide concise, helpful answers to users seeking guidance on these topics.
Always cite the blog post titles and URLs you reference using markdown syntax for transparency.
Feel free to sprinkle in a few emojis to keep the conversation light and engaging.

Use only the information available in your knowledge base. Avoid making assumptions, referring to external sources, or generating information not explicitly provided.

Remind users that for serious health concerns, it's essential to consult a medical professional.
If you don't know the answer, simply say so.
</instruction>
"""


CONTEXT_TEMPLATE: str = """
<context>
Here is a list of blog posts and their relevant paragraphs that have been retrieved from your knowledge base based on the most recent message posted by the user:

{context}

</context>
"""


WELCOME_MSG: str = """
Hi **{user_name}**! 🌟 Welcome to your personalized guide for healthy eating and lifestyle habits! I'm here to provide you with science-backed insights straight from the vast knowledge base of [Dr. Michael Greger & his team](https://nutritionfacts.org/team/)
at [NutritionFacts.org](https://nutritionfacts.org/about/). Whether you're curious about nutrition, seeking advice, or just looking to make informed choices, I'm here to support you every step of the way on your journey to a healthier, happier life. Let's dive in! 💚
"""


def build_system_msg(context: str) -> str:
    return BOT_INSTRUCTION + CONTEXT_TEMPLATE.format(context=context)


def extract_context_from_msg(text: str) -> str | None:
    """
    Extracts and returns the text between <context> and </context> tags.


    Parameters
    ----------
    text : str
        The input string containing the context tags.

    Returns
    -------
    str | None
        The extracted text between the context tags, or None if no match is found.
    """
    # Regular expression to find text between <context> and </context>
    pattern = r"<context>(.*?)</context>"

    # Search for the pattern
    match = re.search(pattern, text, re.DOTALL)

    # Return the extracted text if a match is found, otherwise return None
    if match:
        return match.group(1)

    return None
