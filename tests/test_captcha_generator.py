import unittest
import unittest.mock
import time
import pandas as pd
from open_captcha.common_types import Challenge, ServerContext
from open_captcha.captcha_generator import (
    _get_timestamp, _generate_challenge_id, _verify_timeout, _verify_text_is_close, CaptchaGenerator
)
from tests.fake_template import QuestTemplate


class HelperFunctionsTest(unittest.TestCase):
    def test_get_timestamp(self):
        t = _get_timestamp()
        self.assertIsInstance(t, int)
        time.sleep(1.1)
        t2 = _get_timestamp()
        self.assertGreaterEqual(t2 - t, 1)
        self.assertLessEqual(t2 - t, 3)

    def test_generate_challenge_id(self):
        challenge_ids = {_generate_challenge_id() for _ in range(10)}
        self.assertEqual(len(challenge_ids), 10)  # no duplicates
        for cid in challenge_ids:
            assert isinstance(cid, str)
            self.assertEqual(len(cid), 32)

    @unittest.mock.patch('open_captcha.captcha_generator._get_timestamp')
    def test_verify_timeout(self, mock_get_timestamp):
        t0 = 100
        delta = 10
        mock_get_timestamp.return_value = t0 + delta
        self.assertEqual(_verify_timeout(t0, timeout=delta), True)
        mock_get_timestamp.assert_called_once_with()
        self.assertEqual(_verify_timeout(t0, timeout=delta - 1), False)

    def test_verify_text_is_close(self):
        self.assertEqual(_verify_text_is_close('abcde', 'abcde', 5), True)
        self.assertEqual(_verify_text_is_close('abcde', 'abc', 5), False)
        self.assertEqual(_verify_text_is_close('abcde', 'XbcdX', 5), False)
        self.assertEqual(_verify_text_is_close('abcdef', 'XbcdXf', 5), True)
        self.assertEqual(_verify_text_is_close('abcde', 'XbcdX', 4), True)
        self.assertEqual(_verify_text_is_close('abcd', 'XbcdX', 4), False)


class CaptchaGeneratorTest(unittest.TestCase):
    def setUp(self):
        super().setUp()

        self.data = {
            'report_counts': [
                dict(city_name='New York', num_symptoms=9666, num_deaths=123),
                dict(city_name='Los Angeles', num_symptoms=5000, num_deaths=23),
                dict(city_name='Boston', num_symptoms=800, num_deaths=250),
                dict(city_name='Detroit', num_symptoms=0, num_deaths=1),
                dict(city_name='West Yellowstone', num_symptoms=5, num_deaths=2),
            ]
        }

        self.template_configs = [
            ('quest', dict()),
            ('quest', dict(quest='peace')),
            ('quest', dict(quest='some quiet')),
        ]
        self.mock_timeout = unittest.mock.Mock()
        self.mock_typos = unittest.mock.Mock()
        self.mock_rendering_options = unittest.mock.Mock()

    def _get_captcha_generator(self, data, template_configs, verify_config=True):
        return CaptchaGenerator(
            data=data,
            template_configs=template_configs,
            response_timeout_sec=self.mock_timeout,
            num_letters_per_allowed_typo=self.mock_typos,
            verify_config=verify_config
        )

    @unittest.mock.patch('open_captcha.captcha_generator.RNG')
    def test_configuration_sanity(self, mock_RNG):
        captcha = self._get_captcha_generator(self.data, self.template_configs)
        self.assertEqual(captcha.data.keys(), {'report_counts'})
        pd.testing.assert_frame_equal(
            captcha.data['report_counts'],
            pd.DataFrame.from_records(self.data['report_counts'])
        )
        self.assertEqual(len(captcha.templates), len(self.template_configs))
        for template in captcha.templates:
            self.assertIsInstance(template, QuestTemplate)
        mock_RNG.assert_called_once_with(None)
        self.assertEqual(captcha._non_crypto_rng, mock_RNG.return_value)

    def test_bad_configs(self):
        template_configs = [
            ('quest', dict()),
            ('quest', dict(quest='peace', error_msg='boom!')),
        ]
        self._get_captcha_generator(self.data, template_configs, verify_config=False)
        with self.assertRaisesRegex(Exception, 'boom!'):
            self._get_captcha_generator(self.data, template_configs)

    @unittest.mock.patch('open_captcha.captcha_generator._get_timestamp')
    @unittest.mock.patch('open_captcha.captcha_generator._generate_challenge_id')
    def test_generate_challenge(self, mock_generate_challenge_id, mock_get_timestamp):
        # Arrange
        silly_challenge = Challenge('stuff', b'some bytes', ['A', 'B', 'C'])
        correct_answer = 'correct!'
        mock_template = unittest.mock.Mock()
        mock_template.generate_challenge.return_value = silly_challenge, correct_answer
        mock_rng = unittest.mock.Mock()
        mock_rng.choice.return_value = mock_template
        captcha = self._get_captcha_generator(self.data, self.template_configs)
        captcha._non_crypto_rng = mock_rng
        attempt_number = 666

        # Act
        challenge_id, challenge, context = captcha.generate_challenge(attempt_number, self.mock_rendering_options)

        # Assert
        mock_template.generate_challenge.assert_called_once_with(captcha.data, mock_rng, self.mock_rendering_options)
        self.assertEqual(challenge_id, mock_generate_challenge_id.return_value)
        self.assertEqual(challenge, silly_challenge)
        expected_context = ServerContext(
            timestamp=mock_get_timestamp.return_value,
            verification_attempt_number=attempt_number,
            correct_answer=correct_answer
        )
        self.assertEqual(context, expected_context)

    @unittest.mock.patch('open_captcha.captcha_generator._verify_text_is_close')
    @unittest.mock.patch('open_captcha.captcha_generator._verify_timeout')
    def test_verify_response(self, mock_verify_timeout, mock_verify_text):
        captcha = self._get_captcha_generator(self.data, self.template_configs)
        context = ServerContext(
            timestamp=456,
            verification_attempt_number=666,
            correct_answer='42'
        )
        user_answer = 'The butler did it'

        def check(timeout_ok, text_ok):
            mock_verify_timeout.reset_mock()
            mock_verify_text.reset_mock()
            mock_verify_timeout.return_value = timeout_ok
            mock_verify_text.return_value = text_ok
            is_ok = captcha.verify_response(user_answer, context)
            self.assertEqual(is_ok, timeout_ok and text_ok)
            mock_verify_timeout.assert_called_once_with(context.timestamp, self.mock_timeout)
            if timeout_ok:
                mock_verify_text.assert_called_once_with(context.correct_answer, user_answer, self.mock_typos)
            else:
                mock_verify_text.assert_not_called()

        check(False, False)
        check(False, True)
        check(True, False)
        check(True, True)


if __name__ == '__main__':
    unittest.main()
