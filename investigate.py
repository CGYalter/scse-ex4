## Import the necessary modules
import json

## Import the function from the module parse_data
from parse_data import load_items, get_unclaimed_items, save_result

import ollama

## Name of the Qwen model served by Ollama (change if a different one is pulled).
MODEL = "qwen2.5"


## Build your prompt based on the description the user provides
## and the items that are available in the lost-and-found database.
## The model must follow the rules listed in the README file
## The function should return the system prompt and the user prompt.
## You may need to use json.dumps() to convert the available_items list into a JSON string.
def build_prompt(description, available_items):
    system_prompt = (
        "You are a campus lost-and-found assistant. "
        "Given a description of a lost item and a JSON list of items in the "
        "lost-and-found database, find every item that is a possible match. "
        "Not all the details of an item must match for it to be a possible match. "
        "Use ONLY the given JSON data; do not invent items. "
        'Return ONLY valid JSON with exactly the following structure: '
        '{"matches": ["ITEM_ID"], "confidence": "LOW"}. '
        '"matches" must contain the IDs of all the possible matching items '
        '(an empty list if there is no match). '
        '"confidence" must be exactly one of: LOW, MEDIUM, HIGH.'
    )

    user_prompt = (
        f"Description of the lost item: {description}\n\n"
        "Items in the lost-and-found database:\n"
        f"{json.dumps(available_items, indent=2)}"
    )

    return system_prompt, user_prompt


## Logic to ask Qwen for all the possible matches based on the system prompt and user prompt.
## The function should return the response from Qwen.
def ask_qwen(system_prompt, user_prompt):
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response["message"]["content"]


## Logic to parse the response from Qwen and return the result.
## You may need to use json.loads() to convert the response string into a suitable Python data structure.
def parse_response(response_text):
    text = response_text.strip()

    # Strip markdown code fences if the model wrapped the JSON in ```json ... ```.
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    return json.loads(text)


## Logic to validate the result returned by Qwen.
## It should check if the result is a dictionary, contains the keys "matches" and "confidence", and that the values are of the correct type.
## If everything is correct, then it should check if the item IDs in the "matches" list are valid IDs .
def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False
    if "matches" not in result or "confidence" not in result:
        return False
    if not isinstance(result["matches"], list):
        return False
    if result["confidence"] not in ("LOW", "MEDIUM", "HIGH"):
        return False

    valid_ids = {item["id"] for item in available_items}
    for item_id in result["matches"]:
        if item_id not in valid_ids:
            return False

    return True


## Logic to display the matches found by Qwen in a user-friendly format.
## It should look something like this:
"""
CAMPUS LOST-AND-FOUND ASSISTANT
==================================================

Describe the item you lost: I lost a black bag somewhere

Searching for possible matches...

MATCH RESULT
--------------------------------------------------
Confidence: MEDIUM

Possible matches:

ID: F101
Item: backpack
Color: black
Location: Library 2nd floor
Date found: 2026-09-15

Result saved to output/match_result.json
 """
## If no matches are found, it should display a message indicating that no matches were found, along with the empty list
def display_matches(result, available_items):
    print("\nMATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")

    matches = result["matches"]
    if not matches:
        print("\nNo matches were found.")
        print("Matches: []")
        return

    items_by_id = {item["id"]: item for item in available_items}
    print("\nPossible matches:")
    for item_id in matches:
        item = items_by_id[item_id]
        print()
        print(f"ID: {item['id']}")
        print(f"Item: {item['item']}")
        print(f"Color: {item['color']}")
        print(f"Location: {item['location']}")
        print(f"Date found: {item['date']}")


## Control center for the entire program.
def main():
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    print()

    items = load_items("found_items.json")
    available_items = get_unclaimed_items(items)

    description = input("Describe the item you lost: ")
    print("\nSearching for possible matches...")

    system_prompt, user_prompt = build_prompt(description, available_items)
    response_text = ask_qwen(system_prompt, user_prompt)
    result = parse_response(response_text)

    if not validate_result(result, available_items):
        print("\nThe model returned an invalid result. Please try again.")
        return

    display_matches(result, available_items)

    save_result(result, "output/match_result.json")
    print("\nResult saved to output/match_result.json")


if __name__ == "__main__":
    main()
