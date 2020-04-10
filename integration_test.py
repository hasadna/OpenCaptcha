import unittest
import json
import textwrap
from common_types import ServerContext
from captcha_generator import CaptchaGenerator


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        data = {
            'report_counts': [
                dict(city_name='New York', num_symptoms=9666, num_deaths=123),
                dict(city_name='Los Angeles', num_symptoms=5000, num_deaths=23),
                dict(city_name='Boston', num_symptoms=800, num_deaths=250),
                dict(city_name='Detroit', num_symptoms=0, num_deaths=1),
                dict(city_name='West Yellowstone', num_symptoms=5, num_deaths=2),
            ]
        }

        template_configs_json = textwrap.dedent("""\
        [
            ["bar", {
                "question": "These {n} cities had the most reported symptoms yesterday. Which city reported the most symptoms?",
                "table": "report_counts",
                "labels": "city_name",
                "values": "num_symptoms",
                "n": 3
            }],
            ["bar", {
                "question": "These {n} cities had the most reported deaths yesterday. Which city reported the most deaths?",
                "table": "report_counts",
                "labels": "city_name",
                "values": "num_deaths",
                "n": 4
            }]
        ]""")
        template_configs = json.loads(template_configs_json)
        self.captcha = CaptchaGenerator(data, template_configs, response_timeout_sec=180)

    def test_full_flow_sanity(self):
        all_challenge_ids = set()
        all_variants = set()
        for _ in range(10):
            challenge_id, challenge, context = self.captcha.generate_challenge()
            all_challenge_ids.add(challenge_id)
            saved_context_json = context.to_json()
            loaded_context = ServerContext.from_json(saved_context_json)
            if 'symptoms' in challenge.question:
                all_variants.add('symptoms')
                self.assertEqual(set(challenge.possible_answers), {'New York', 'Los Angeles', 'Boston'})
                self.assertEqual(self.captcha.verify_response('Los Angeles', loaded_context), False)
                self.assertEqual(self.captcha.verify_response('Potato!', loaded_context), False)
                self.assertEqual(self.captcha.verify_response('New York', loaded_context), True)
            else:
                all_variants.add('deaths')
                self.assertEqual(set(challenge.possible_answers), {'New York', 'Los Angeles', 'Boston', 'West Yellowstone'})
                self.assertEqual(self.captcha.verify_response('New York', loaded_context), False)
                self.assertEqual(self.captcha.verify_response('Wuhan', loaded_context), False)
                self.assertEqual(self.captcha.verify_response('Boston', loaded_context), True)
        self.assertEqual(len(all_challenge_ids), 10)
        self.assertEqual(all_variants, {'symptoms', 'deaths'})


if __name__ == '__main__':
    unittest.main()
