"""Live integration checks: start Python and Go first; no test libraries needed."""
import json
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError

BASE = "http://127.0.0.1:8082"


def get(path, **params):
    with urlopen(BASE + path + "?" + urlencode(params), timeout=30) as response:
        return json.load(response)


cases = [
    ("Who loved football?", "", "answered", "mani", "football"),
    ("When did Nika join the protests?", "", "answered", "nika", "20 September 2022"),
    ("When did she join the protests?", "nika", "answered", "nika", "20 September 2022"),
    ("When was Khodanoor detained?", "", "answered", "khodanoor", "July 2022"),
    ("Was the rescuer in the video definitely Hamid?", "", "answered", "hamid", "certainty"),
    ("What was Nika's favorite pizza topping?", "", "not_found", "nika", ""),
    ("What football team did Nika support?", "", "not_found", "nika", ""),
    ("When did Nika first ever attend a protest?", "", "not_found", "nika", ""),
    ("What is the weather tomorrow?", "", "not_found", "", ""),
    ("When did they go out in protest?", "", "clarify", "", ""),
    ("When did Nika and Mani protest?", "", "clarify", "", ""),
]
for question, person, status, expected_person, fragment in cases:
    answer = get("/api/ask", q=question, person_id=person)
    assert answer["status"] == status, (question, answer)
    assert answer["person_id"] == expected_person, (question, answer)
    assert fragment in answer["answer"], (question, answer)
    if status == "answered":
        assert answer["sources"] and all(s["url"].startswith("https://") for s in answer["sources"])
        assert answer["matched_text"] in answer["answer"]
    else:
        assert answer["sources"] == []
    print("PASS", question)
assert get("/api/search", q="Who loved football?", limit=3)["results"][0]["id"] == "mani"
for query, person, code in [(" ", "", 400), ("x" * 301, "", 400), ("Who was she?", "missing", 404)]:
    try:
        get("/api/ask", q=query, person_id=person)
        raise AssertionError("Invalid request accepted")
    except HTTPError as error:
        assert error.code == code
print("PASS search ranking and input validation")
