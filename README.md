# OpenCaptcha
Leverage the open information collected in the project to a bots blocker mechanism

![image](https://user-images.githubusercontent.com/3581741/78539426-38b36900-77fb-11ea-9b8a-db95052caba1.png)


[draw.io link](https://drive.google.com/file/d/1V6jYpukxYDqc_ESqOleOh2kCvGFfs2Ah/view?usp=sharing)


Build a mechanism to differentiate relatively safe/approved records from suspicious submissions, to protect the database from bots and automated submissions.


### Generate Fact from Data
#### Data
For example, yesterday or last week's (approved, nonsuspicious) records, JSON.

#### Q&A Templates
A list of Questions and Answers given the mentioned data. 

The question should have two parts: 
- A graphical representation of the challenge 
- A textual label + multi selection question

(note: both parts should fit the multilingual nature of the project, and should be connected to the translation mechanism)

For example:

|שאלה| נוסחה חתשובה| סוג השאלה|הערות|
|-----|------|-------|----|
| אלו 3 הערים בהן דווחו הכי הרבה סימפטומים אתמול. מי העיר עם הכי הרבה סימפטומים?| `max(record.city `)| bar_question| |
| 394 אנשים דיווחו על שיעול היום בתל אביב. האם מספר המדווחים על שיעול עלה או ירד| `line(symptoms.cough)` | line question | "

### Draw Fact
This part will draw the fact by the question type
- bar question
- pie question
- line question

(note again: drawing the fact should consider the multilingual nature of the site, and use the relevant language based on the user UI)

And will hold until the user answers: notice - the answer should be typed in manually, based on the given options in the question body.

i.e.

question: "באיזו מבין הערים/ישובים דווחו הכי הרבה אנשים עם שיעול?" (show graph)
options: " רחובות |  בנימינה | תל-שבע"

the typed in the answer would be "בנימינה", typed in as a textual string

###  Ask User About Fact
The server:
1. creates a unique question based on the data from a predefined set of templates. The template defines:
   - text template for question
   - text templates for possible answers
   - chart type
1. draws the chart into a bitmap image
1. prepares the template values for the question and answers
1. generates a random 128 bit challenge_id and the following context associated with it:
    - timestamp
    - correct answer
    - verification attempt number
1. saves the context to cache (e.g. redis), keyed by the challenge_id and with a TTL of a few minutes (longer than the max time we allow for the user to answer) 
1. sends to the client:
   - challenge_id
   - the chart
   - question & possible answers

The client then
1. shows the chart to the user
1. renders the question and answers based on the values and template
1. waits for user input
1. when submitting the report, the client sends the server with the report data also:
   - challenge_id
   - user's typed answer

The server finally:
1. retrieves and deletes the associated context from the cache. 
If the context is not found (either because the TTL has passed or because an answer has already been received for this challenge_id(*))
then the response is considered suspicious.
1. verifies the timestamp (not too old)
1. verifies the answer matches the correct answer in the context (up to small diff due to typos or alternative spelling)
1. saves the report to the db (in suspicious bucket or regular one).
If we want to give users more than one attempt, we can generate another challenge
and increment the attempt number saved with the context. The logic for how many attempts
to provide and whether to track multiple attempts as slightly suspicious is left
to the broader server logic.

(*) If we want to differentiate between late responses and multiple responses for same 
challenge_id (which is even more suspicious) then we can save the used challenge IDs in a 
separate cache with a longer TTL and check against that when a challenge ID is not found in the 
regular cache.