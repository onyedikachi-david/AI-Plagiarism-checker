import requests
from flask import Flask

def confidenceToPercent(original, plagiarism):
    return plagiarism * 100, original * 100

def grading(original, plagiarism):
    p, o = confidenceToPercent(original, plagiarism)
    return p, o

app = Flask(__name__)

response = requests.post(
    "https://jpwahle-plagiarism-detection.hf.space/run/predict",
    json={
        "data": [
            "The North Pacific right whale seems to happen in two populaces. The populace in the eastern North Pacific/Bering Sea is amazingly low, numbering around 30 people. A bigger western populace of 100Ã¢ÂÂ 200 seems, by all accounts, to be making due in the Sea of Okhotsk, yet next to no is thought about this populace. In this manner, the two northern right whale species are the most jeopardized of every extensive whale and two of the most imperiled creature species on the planet. In light of current populace thickness patterns, the two species are anticipated to end up wiped out inside 200 years. The Pacific species was truly found in summer from the Sea of Okhotsk in the west to the Gulf of Alaska in the east, for the most part north of 50ÃÂ°N. Today, sightings are exceptionally uncommon and for the most part happen in the mouth of the Sea of Okhotsk and in the eastern Bering Sea. In spite of the fact that this species is all around prone to be transitory like the other two species, its development designs are not known."
        ]
    },
).json()

data = response["data"]
original_confidence = data[0]["confidences"][0]["confidence"]
plagiarism_confidence = data[0]["confidences"][1]["confidence"]

p, o = grading(original_confidence, plagiarism_confidence)

print(data)
print(f"Plagiarism confidence: {plagiarism_confidence}%")
print(f"Originality confidence: {original_confidence}%")
print(f"Percentage of Plagiarism: {round(p)}%")
print(f"Percentage of Originality:{round(o)}%")


@app.route("/")
def main():
    return str(data)

if __name__ == "__main__":
    app.run()
