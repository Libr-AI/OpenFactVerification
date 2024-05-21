decompose_prompt = """
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

# restore_prompt = """Given a text and a list of facts derived from the text, your task is to identify the corresponding words in the text that derive each fact.
# For each fact, please find the minimal continues span in the original text that contains the information to derive the fact. The answer should be a JSON dict where the keys are the facts and the values are the corresponding spans copied from the original text.
#
# For example,
# Text: Mary is a five-year old girl, she likes playing piano and she doesn't like cookies.
# Facts: ["Mary is a five-year old girl.", "Mary likes playing piano.", "Mary doesn't like cookies."]
#
# Output:
# {{"Mary is a five-year old girl.":"Mary is a five-year old girl",
# "Mary likes playing piano.":"she likes playing piano",
# "Mary doesn't like cookies.":"she doesn't like cookies."]
#
# Text: {doc}
# Facts: {claims}
# Output:
# """

# use this for demo
restore_prompt = """Given a text and a list of facts derived from the text, your task is to split the text into chunks that derive each fact.
For each fact, please find the corresponding continues span in the original text that contains the information to derive the fact. The answer should be a JSON dict where the keys are the facts and the values are the corresponding spans copied from the original text.
Please make sure the returned spans can be concatenated to the full original doc.

For example,
Text: Mary is a five-year old girl, she likes playing piano and she doesn't like cookies.
Facts: ["Mary is a five-year old girl.", "Mary likes playing piano.", "Mary doesn't like cookies."]

Output:
{{"Mary is a five-year old girl.":"Mary is a five-year old girl,",
"Mary likes playing piano.":"she likes playing piano",
"Mary doesn't like cookies.":"and she doesn't like cookies."]

Text: {doc}
Facts: {claims}
Output:

"""

checkworthy_prompt = """
Your task is to evaluate each provided statement to determine if it presents information whose factuality can be objectively verified by humans, irrespective of the statement's current accuracy. Consider the following guidelines:
1. Opinions versus Facts: Distinguish between opinions, which are subjective and not verifiable, and statements that assert factual information, even if broad or general. Focus on whether there's a factual claim that can be investigated.
2. Clarity and Specificity: Statements must have clear and specific references to be verifiable (e.g., "he is a professor" is not verifiable without knowing who "he" is).
3. Presence of Factual Information: Consider a statement verifiable if it includes factual elements that can be checked against evidence or reliable sources, even if the overall statement might be broad or incorrect.
Your response should be in JSON format, with each statement as a key and either "Yes" or "No" as the value, along with a brief rationale for your decision.

For example, given these statements:
1. Gary Smith is a distinguished professor of economics.
2. He is a professor at MBZUAI.
3. Obama is the president of the UK.

The expected output is:
{{
    "Gary Smith is a distinguished professor of economics.": "Yes (The statement contains verifiable factual information about Gary Smith's professional title and field.)",
    "He is a professor at MBZUAI.": "No (The statement cannot be verified due to the lack of clear reference to who 'he' is.)",
    "Obama is the president of the UK.": "Yes (This statement contain verifiable information regarding the political leadership of a country.)"
}}

For these statements:
{texts}

The output should be:
"""

qgen_prompt = """Given a claim, your task is to create minimum number of questions need to be check to verify the correctness of the claim. Output in JSON format with a single key "Questions", the value is a list of questions. For example:

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

verify_prompt = """
Your task is to decide whether the evidence supports, refutes, or is irrelevant to the claim. Carefully review the evidence, noting that it may vary in detail and sometimes present conflicting information. Your judgment should be informed by this evidence, taking into account its relevance and reliability.
Please structure your response in JSON format, including the following four keys:
- "reasoning": explain the thought process behind your judgment.
- "relationship": the stance label, which can be one of "SUPPORTS", "REFUTES", or "IRRELEVANT".
For example,
Input:
[claim]: MBZUAI is located in Abu Dhabi, United Arab Emirates.
[evidence]: Where is MBZUAI located?\nAnswer: Masdar City - Abu Dhabi - United Arab Emirates
Output:
{{
    "reasoning": "The evidence confirms that MBZUAI is located in Masdar City, Abu Dhabi, United Arab Emirates, so the relationship is SUPPORTS.",
    "relationship": "SUPPORTS"
}}
Input:
[claim]: Copper reacts with ferrous sulfate (FeSO4).
[evidence]: Copper is less reactive metal. It has positive value of standard reduction potential. Metal with high standard reduction potential can not displace other metal with low standard reduction potential values. Hence copper can not displace iron from ferrous sulphate solution. So no change will take place.
Output:
{{
    "reasoning": "The evidence provided confirms that copper cannot displace iron from ferrous sulphate solution, and no change will take place. Therefore, the evidence refutes the claim",
    "relationship": "REFUTES"
}}
Input:
[claim]: Apple is a leading technology company in UK.
[evidence]: International Business Machines Corporation, nicknamed Big Blue, is an American multinational technology company headquartered in Armonk, New York and present in over 175 countries.
Output:
{{
    "reasoning": "The evidence is about IBM, while the claim is about Apple. Therefore, the evidence is irrelevant to the claim",
    "relationship": "IRRELEVANT"
}}
Input
[claim]: {claim}
[evidences]: {evidence}
Output:
"""


class ChatGPTPrompt:
    decompose_prompt = decompose_prompt
    restore_prompt = restore_prompt
    checkworthy_prompt = checkworthy_prompt
    qgen_prompt = qgen_prompt
    verify_prompt = verify_prompt
