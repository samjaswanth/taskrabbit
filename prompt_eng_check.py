from openai import OpenAI
import httpx
import json


OPENAI_API_KEY = ""
client = OpenAI(api_key=OPENAI_API_KEY, http_client=httpx.Client(verify=False))


a = {
    '1234': {'doc_id': "1234", 'name': "jaswanth", 'address':'34, kumudam, anupuram, chennai'},
    '5678': {'doc_id': "5678", 'name': "rad", 'address':'123, kcg post, coimbatore'}
}

input_dict = {'name': "jas", 'address':'amman nagar chennai'}


prompt = f"""
You are a smart comparison engine.

You are given a Python dictionary `a`:

a = {json.dumps(a, indent=2)}

And an input dictionary:

input_dict = {json.dumps(input_dict, indent=2)}

Check if the `input_dict` semantically matches any of the entries in `a`, especially comparing the `name` and `address` fields. Allow minor differences like abbreviations, different formatting, or synonymous phrases (e.g., 'door no.34' and '34').

If a match is found No explanation is needed, just give the output dictionary, reply with:
{{ "doc_id": "...", "name": "..." }} 

Otherwise, reply with:
False
Don give any explanation
"""


response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a Python code reasoning assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0
)

# Result
decision = response.choices[0].message.content.strip()
print("Match found:", decision)
