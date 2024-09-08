# Project Context

## Short Project overview

This is a RAG-based Q&A Chatbot about healthy eating & lifestyle habits

This is a chatbot intended to help answer questions around a healthy eating and lifestyle habits.

This chatbot (aka digital twin of the physician [Dr. Michael Greger & his team](https://nutritionfacts.org/team/)) will help answer any question you may have about healthy eating and living from the perspective of the science-based nonprofit organization [NUTRITIONFACTS.ORG](https://nutritionfacts.org/about/), which has over 1200 well-researched blog posts since 2011.

## Questions

1. **What is the main problem your project is trying to solve?**
   - Being able to ask simple question related  to healthy eating and living to health professional easily.
   - Why is this problem important or relevant?
        - Getting access to reliable information for non-medical professionals may be difficult as it requires usually to book appointments. Moreover, the internet is full of false or misleading information and a non-medical professionals is not able to judge the quality of information.

2. **Who is the target audience or end-user for this project?**
   - Are there specific industries, groups, or individuals that would benefit from this solution?

3. **What is the context or background of the problem?**
   - People may be misinformed about healthy eating and living and may not have access to reliable information.
   - Is this problem new or part of an ongoing challenge?
    - It's an ongoing challenge to get access to reliable information.
   - Is there existing research or data that highlights the importance of this issue?
    - There is evidence that with healthy eating and living less medical attention is needed for individuals.

4. **How does your project address the problem?**
   - What approach or methodology are you using? Is there a specific technology, tool, or technique that's central to your solution?
    - RAG-based Q&A Chatbot that is build on the 1200 well-researched blog posts of the science-based nonprofit organization [NUTRITIONFACTS.ORG](https://nutritionfacts.org/about/) run by the physician [Dr. Michael Greger & his team](https://nutritionfacts.org/team/)).

5. **What are the expected outcomes or benefits of your solution?**
   - What changes or improvements do you expect as a result of your project?
    - People become more educate about healthy eating and living, they making more informed decisions about healthy eating and living and ideal have a healthy, happier life and need less medical attention. They may also influence other and educate them on healthy eating and living. In the long therm this could also relieve our health system, since less people need to seek medical attention.

6. **Are there any limitations or challenges that your project faces?**
   - This could include technical limitations, scope limitations, or any challenges related to data availability or implementation.
   - The context retriever may not be able to provide relevant context information given a user input, which can lead the LLM to produce false or misleading information.
   - LLM can hallucinant on its own even with the right context information and may create a false or misleading information.
   - For both problems, there a solutions to mitigate them but at the current state of technology it's difficult to avoid them.
   -

### Problem Description from chatgpt

Access to reliable and accurate information on healthy eating and lifestyle habits is a significant challenge for the general public. Although many individuals seek to improve their health by making informed choices, they often face obstacles in obtaining trustworthy advice. The internet is saturated with conflicting and sometimes misleading information, making it difficult for non-medical professionals to discern the quality and credibility of the sources. Additionally, accessing professional advice typically requires scheduling appointments with healthcare providers, which can be time-consuming and costly.

This project aims to bridge this gap by providing a RAG-based Q&A chatbot that offers reliable, science-backed answers to questions related to healthy eating and lifestyle habits. The chatbot serves as a digital twin of Dr. Michael Greger and his team at NutritionFacts.org, a well-respected, science-based nonprofit organization dedicated to sharing evidence-based insights on nutrition. By leveraging over 1,200 thoroughly researched blog posts, this chatbot empowers users to obtain accurate and actionable information easily.

The primary goal of this project is to educate individuals about healthy living, enabling them to make informed decisions that could lead to healthier, happier lives with reduced reliance on medical interventions. In the long term, widespread use of this tool could contribute to alleviating the burden on the healthcare system by promoting preventative health practices.

However, the project faces certain limitations. The context retriever may occasionally fail to provide relevant information, leading the LLM (Language Model) to generate inaccurate or misleading responses. Additionally, the inherent risk of LLM hallucinations, where the model fabricates information, presents a challenge. While there are strategies to mitigate these risks, completely eliminating them remains difficult with current technology.
