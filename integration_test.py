import unittest
import json
import os
import textwrap
from common_types import ServerContext, RenderingOptions
from captcha_generator import CaptchaGenerator
from challenge_templates import render_bar_chart


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.data = {
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
            ["min-max-bar", {
                "question": "These {n} cities had the most reported symptoms yesterday. Which city reported the most symptoms?",
                "table": "report_counts",
                "labels": "city_name",
                "values": "num_symptoms",
                "variant": "max",
                "n": 3
            }],
            ["min-max-bar", {
                "question": "These {n} cities had the most reported deaths yesterday. Which city reported the most deaths?",
                "table": "report_counts",
                "labels": "city_name",
                "values": "num_deaths",
                "variant": "max",
                "n": 4
            }]
        ]""")
        self.template_configs = json.loads(template_configs_json)
        self.captcha = CaptchaGenerator(self.data, self.template_configs, response_timeout_sec=180)

    @staticmethod
    def _save_image(image_bytes, name):
        path = os.path.abspath(f'{name}.png')
        print(f'Writing image to {path}')
        with open(path, 'wb') as f:
            f.write(image_bytes)

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
                self.assertEqual(self.captcha.verify_response('New Yorx', loaded_context), True)
            else:
                all_variants.add('deaths')
                self.assertEqual(set(challenge.possible_answers), {'New York', 'Los Angeles', 'Boston', 'West Yellowstone'})
                self.assertEqual(self.captcha.verify_response('New York', loaded_context), False)
                self.assertEqual(self.captcha.verify_response('Wuhan', loaded_context), False)
                self.assertEqual(self.captcha.verify_response('Boston', loaded_context), True)
                self.assertEqual(self.captcha.verify_response('Bostn', loaded_context), True)
        self.assertEqual(len(all_challenge_ids), 10)
        self.assertEqual(all_variants, {'symptoms', 'deaths'})

    def test_full_flow_with_image(self):
        template_configs = self.template_configs[:1]  # Ensure we use the symptoms challenge.
        captcha = CaptchaGenerator(self.data, template_configs, response_timeout_sec=180, rng_seed=0)
        options = RenderingOptions(figure_size=(4, 3))
        _, challenge, _ = captcha.generate_challenge(rendering_options=options)
        expected_chart = render_bar_chart([
            ('Boston', 800),
            ('New York', 9666),
            ('Los Angeles', 5000)
        ], options=options)
        if challenge.chart != expected_chart:
            # Save expected vs actual image for manual inspection / debugging.
            self._save_image(expected_chart, 'expected-chart')
            self._save_image(challenge.chart, 'actual-chart')
        self.assertEqual(challenge.chart, expected_chart)


if __name__ == '__main__':
    unittest.main()
