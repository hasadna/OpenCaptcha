import sys
import pytest
import unittest
import unittest.mock
import pandas as pd
from open_captcha.common_types import CaptchaError, RenderingOptions, RNG
from open_captcha.challenge_templates import (
    UnknownTemplate, BadTemplateParameters, ConfigurationError, MinMaxBarTemplate,
    get_class_by_name_mapping, instantiate_one_template, instantiate_templates,
    render_bar_chart,
)
from tests.paths import data_file
from tests.fake_template import QuestTemplate


class TemplateRegistrationTest(unittest.TestCase):
    def test_get_class_by_name_mapping(self):
        class_by_name = get_class_by_name_mapping()
        self.assertEqual(class_by_name['quest'], QuestTemplate)
        self.assertEqual(class_by_name['min-max-bar'], MinMaxBarTemplate)

    @unittest.mock.patch.object(QuestTemplate, 'config_name', 'min-max-bar')
    def test_get_class_by_name_mapping_conflict(self):
        with self.assertRaisesRegex(CaptchaError, 'Config name min-max-bar used by both'):
            get_class_by_name_mapping()

    def test_instantiate_one_template(self):
        cls_by_name = get_class_by_name_mapping()

        # Check name not found
        with self.assertRaises(UnknownTemplate):
            instantiate_one_template(cls_by_name, ('nosuch', {}))

        # Instantiate quest with default and non-default parameters
        quest = instantiate_one_template(cls_by_name, ('quest', {}))
        self.assertIsInstance(quest, QuestTemplate)
        self.assertEqual(quest.answer, 'to find the holy grail')
        quest = instantiate_one_template(cls_by_name, ('quest', {'quest': 'some cheese'}))
        self.assertIsInstance(quest, QuestTemplate)
        self.assertEqual(quest.answer, 'to find some cheese')

        # Wrong parameters
        with self.assertRaises(BadTemplateParameters):
            instantiate_one_template(cls_by_name, ('quest', {'favorite_color': 'blue'}))

    def test_instantiate_templates(self):
        templates = instantiate_templates([
            ('quest', {}),
            ('quest', {'quest': 'some cheese'}),
        ])
        self.assertEqual(len(templates), 2)
        for t in templates:
            self.assertIsInstance(t, QuestTemplate)
        self.assertEqual(templates[0].answer, 'to find the holy grail')
        self.assertEqual(templates[1].answer, 'to find some cheese')

    def test_instantiate_templates_no_configs(self):
        with self.assertRaisesRegex(ConfigurationError, 'No templates'):
            instantiate_templates([])


class RenderingMethodsTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        # Don't use default_options() so test doesn't break just because defaults were changed.
        self.rendering_options = RenderingOptions(
            figure_size=(6, 4)
        )

    def _load_image(self, name):
        with open(data_file(f'{name}.png'), 'rb') as f:
            return f.read()

    def _save_image(self, name, image_bytes):
        with open(data_file(f'{name}.png'), 'wb') as f:
            return f.write(image_bytes)

    def _verify_chart(self, chart, name, save_on_failure=False):
        expected_chart = self._load_image(name)
        if expected_chart != chart:
            if save_on_failure:
                self._save_image(f'{name}-latest-run', chart)
            raise AssertionError('Image changed from saved version. Run with save_on_failure=True to debug and update.')

    @pytest.mark.skipif('win' not in sys.platform, reason="Need to sort out different expected file on linux")
    def test_render_bar_chart(self):
        label_value_pairs = [('USA', 325), ('China', 1435), ('Italy', 60)]
        chart = render_bar_chart(label_value_pairs, self.rendering_options)
        self._verify_chart(chart, 'bar-chart')


class MinMaxBarTemplateTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.rng = RNG()
        self.data = {
            'report_counts': pd.DataFrame.from_records([
                dict(city_name='New York', num_symptoms=9666, num_deaths=123),
                dict(city_name='Los Angeles', num_symptoms=5000, num_deaths=23),
                dict(city_name='Detroit', num_symptoms=0, num_deaths=1),
                dict(city_name='Boston', num_symptoms=800, num_deaths=250),
                dict(city_name='West Yellowstone', num_symptoms=5, num_deaths=2),
            ])
        }

    def test_config_errors(self):
        with self.assertRaisesRegex(ConfigurationError, 'placeholders'):
            MinMaxBarTemplate(
                question='blerg blerg {nosuch}',
                table='report_counts',
                labels='city_name',
                values='num_symptoms',
                variant='max',
                n=3
            )
        with self.assertRaisesRegex(ConfigurationError, 'variant'):
            MinMaxBarTemplate(
                question='blerg blerg',
                table='report_counts',
                labels='city_name',
                values='num_symptoms',
                variant='nosuch',
                n=3
            )

    @unittest.mock.patch('open_captcha.challenge_templates.render_bar_chart')
    def test_max(self, mock_render):
        mock_options = unittest.mock.Mock()
        question = 'These {n} cities had the most reported symptoms yesterday. Which city reported the most symptoms?'
        template = MinMaxBarTemplate(
            question=question,
            table='report_counts',
            labels='city_name',
            values='num_symptoms',
            variant='max',
            n=3
        )
        challenge, correct_answer = template.generate_challenge(self.data, self.rng, mock_options)
        self.assertEqual(
            challenge.question,
            'These 3 cities had the most reported symptoms yesterday. Which city reported the most symptoms?')
        self.assertEqual(set(challenge.possible_answers), {'New York', 'Los Angeles', 'Boston'})
        self.assertEqual(correct_answer, 'New York')
        mock_render.assert_called_once_with(unittest.mock.ANY, mock_options)
        expected_pairs = {('New York', 9666), ('Los Angeles', 5000), ('Boston', 800)}
        actual_pairs = {(name, value) for name, value in mock_render.call_args_list[0][0][0]}
        self.assertEqual(actual_pairs, expected_pairs)

    @unittest.mock.patch('open_captcha.challenge_templates.render_bar_chart')
    def test_min(self, mock_render):
        mock_options = unittest.mock.Mock()
        question = 'These {n} cities had the least reported symptoms yesterday. Which city reported the least symptoms?'
        template = MinMaxBarTemplate(
            question=question,
            table='report_counts',
            labels='city_name',
            values='num_symptoms',
            variant='min',
            n=3
        )
        challenge, correct_answer = template.generate_challenge(self.data, self.rng, mock_options)
        self.assertEqual(
            challenge.question,
            'These 3 cities had the least reported symptoms yesterday. Which city reported the least symptoms?')
        self.assertEqual(set(challenge.possible_answers), {'West Yellowstone', 'Detroit', 'Boston'})
        self.assertEqual(correct_answer, 'Detroit')
        mock_render.assert_called_once_with(unittest.mock.ANY, mock_options)
        expected_pairs = {('West Yellowstone', 5), ('Detroit', 0), ('Boston', 800)}
        actual_pairs = {(name, value) for name, value in mock_render.call_args_list[0][0][0]}
        self.assertEqual(actual_pairs, expected_pairs)


if __name__ == '__main__':
    unittest.main()
