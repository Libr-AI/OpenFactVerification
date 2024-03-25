# Used prompts
CHECKWORTHY_PROMPT = """
Your task is to determine whether each of the given text is a factual statement (that may be wrong).
Note that:
1. opinion usually not a factual statement (e.g., "love is painful");
2. statement with ambiguous references cannot be treated as a factual statement (e.g., "he is a professor" is not a factual statement without any other reference of "he");
3. if a statement has any factual parts, it should be treated as factual statement. (e.g., "Diego Maradona led Argentina to victory in the 1986 FIFA world cup." contains the factual that "Argentina was victory in the 1986 FIFA world cup").
You should return a JSON with each claim as a key, and "Yes" or "No" (followed by the reason) as the value.

For example, for the following claims (each line is a claim):
1. Gary Smith is a distinguished professor of economics.
2. He is a professor at MBZUAI.
3. Copper (Cu) forms elemental iron when it reacts with ferrous sulphate.
4. It forms elemental iron when it reacts with ferrous sulphate.
5. Georgia is the largest producer of peaches in the United States.
6. Iphone is better than Huawei.
7. LLaMA authors trained smaller versions of the model with fewer parameters than 4.5 billion.
8. Terraform modules can be easily tested.

The output should be:
{{
    "Gary Smith is a distinguished professor of economics.": "Yes",
    "He is a professor at MBZUAI.": "No (We don't know who he is, so it's not possible to judge the factuality of the claim)",
    "Copper (Cu) forms elemental iron when it reacts with ferrous sulphate.": "Yes",
    "It forms elemental iron when it reacts with ferrous sulphate.": "No (ambiguous reference, as we don't know what 'it' means)",
    "Georgia is the largest producer of peaches in the United States.": "Yes",
    "Iphone is better than Huawei.": "No (opinion)",
    "LLaMA authors trained smaller versions of the model with fewer parameters than 4.5 billion.": "Yes",
    "Terraform modules can be easily tested.": "No (opinion)",
}}


For claims:
{texts}

The output should be:
"""

VERIFY_PROMPT = """
Your task is to evaluate the accuracy of a provided statement using the accompanying evidence. Carefully review the evidence, noting that it may vary in detail and sometimes present conflicting information. Your judgment should be informed by this evidence, taking into account its relevance and reliability.

Keep in mind that a lack of detail in the evidence does not necessarily indicate that the statement is inaccurate. When assessing the statement's factuality, distinguish between errors and areas where the evidence supports the statement.

Please structure your response in JSON format, including the following four keys:
- "reasoning": explain the thought process behind your judgment.
- "error": none if the text is factual; otherwise, identify any specific inaccuracies in the statement.
- "correction": none if the text is factual; otherwise, provide corrections to any identified inaccuracies, using the evidence to support your corrections.
- "factuality": true if the given text is factual, false otherwise, indicating whether the statement is factual, or non-factual based on the evidence.

For example:
Input:
[text]: MBZUAI is located in Abu Dhabi, United Arab Emirates.
[evidence]: Where is MBZUAI located?\nAnswer: Masdar City - Abu Dhabi - United Arab Emirates

Output:
{{
    "reasoning": "The evidence confirms that MBZUAI is located in Masdar City, Abu Dhabi, United Arab Emirates, so the statement is factually correct",
    "error": none,
    "correction": none,
    "factuality": true
}}


Input:
[text]: Copper reacts with ferrous sulfate (FeSO4).
[evidence]: Copper is less reactive metal. It has positive value of standard reduction potential. Metal with high standard reduction potential can not displace other metal with low standard reduction potential values. Hence copper can not displace iron from ferrous sulphate solution. So no change will take place.

Output:
{{
    "reasoning": "The evidence provided confirms that copper cannot displace iron from ferrous sulphate solution, and no change will take place.",
    "error": "Copper does not react with ferrous sulfate as stated in the text.",
    "correction": "Copper does not react with ferrous sulfate as it cannot displace iron from ferrous sulfate solution.",
    "factuality": false
}}


Input
[text]: {claim}
[evidences]: {evidence}

Output:
"""

SENTENCES_TO_CLAIMS_PROMPT = """
Your task is to decompose the text into atomic claims.
The answer should be a JSON with a single key "claims", with the value of a list of strings, where each string should be a context-independent claim, representing one fact.
Note that:
1. Each claim should be concise (less than 15 words) and self-contained.
2. Avoid vague references like 'he', 'she', 'it', 'this', 'the company', 'the man' and using complete names.
3. Generate at least one claim for each single sentence in the texts.

For example,
Text: Mary is a five-year old girl, she likes playing piano and she doesn't like cookies.
Output:
{{"claims": ["Mary is a five-year old girl.", "Mary likes playing piano.", "Mary doesn't like cookies."]}}

Text: {doc}
Output:
"""

QGEN_PROMPT = """Given a claim, your task is to create minimum number of questions need to be check to verify the correctness of the claim. Output in JSON format with a single key "Questions", the value is a list of questions. For example:

Claim: Your nose switches back and forth between nostrils. When you sleep, you switch about every 45 minutes. This is to prevent a buildup of mucus. It’s called the nasal cycle.
Output: {{"Questions": ["Does your nose switch between nostrils?", "How often does your nostrils switch?", "Why does your nostril switch?", "What is nasal cycle?"]}}

Claim: The Stanford Prison Experiment was conducted in the basement of Encina Hall, Stanford’s psychology building.
Output:
{{"Question":["Where was Stanford Prison Experiment was conducted?"]}}

Claim: The Havel-Hakimi algorithm is an algorithm for converting the adjacency matrix of a graph into its adjacency list. It is named after Vaclav Havel and Samih Hakimi.
Output:
{{"Questions":["What does Havel-Hakimi algorithm do?", "Who are Havel-Hakimi algorithm named after?"]}}

Claim: Social work is a profession that is based in the philosophical tradition of humanism. It is an intellectual discipline that has its roots in the 1800s.
Output:
{{"Questions":["What philosophical tradition is social work based on?", "What year does social work have its root in?"]}}

Claim: {claim}
Output:
"""