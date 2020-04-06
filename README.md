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
Each question template would define the area of the correct answer to the generated question.
The point the user will click upon will result in a pass/fail of the check. A human user should pass at least one of 3 tries. If not, the record will be marked as suspicious.


I think that it would be better to have the user select out of a few predefined answers instead of clicking on the image (which is error prone).

The server:
a. creates a unique question based on the data from a predefined set of templates
   - template defines: text template for question,text templates for possible answers, chart type
b. draws the chart into a bitmap image
c. generates a unique chart id
d. prepares the template values for the question and answers
e. for each answer generates an encrypted token including the following data:
    - timestamp
    - chart id
    - random number
    - correct (true/false)
f. sends to the client:
    i. the chart
    ii. chart id
    iii. question & answer template identifier and required data
    iv. answer tokens

the client then
g. shows the chart to the user
h. renders the question and answers based on the values and template
i. waits for user input
j. when submitting the report, the client sends the server with the report data also:
   - chart-id
   - selected answer token

the server finally:
k. decrypts the token
l. compares the decrypted chart-id to the one sent from the client
m. verifies the timestamp (not too old)
n. verities it is the correct answer
o. saves the report to the db

An alternative to (j) above would be:
- The client sends just the chart-id and the encrypted token
- The server verifies and returns an encrypted "proof of humanity" / failure
- The client then decides whether to ask the user for another challenge
