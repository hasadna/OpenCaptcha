import unittest
import json
from open_captcha.common_types import ServerContext, RenderingOptions


class RenderingOptionsTest(unittest.TestCase):
    def test_default_options(self):
        options = RenderingOptions.default_options()
        self.assertIsInstance(options, RenderingOptions)


class ServerContextTest(unittest.TestCase):
    def test_json_serialization(self):
        context = ServerContext(
            timestamp=44,
            verification_attempt_number=1,
            correct_answer='forty two'
        )
        context_json = context.to_json()

        # Check direct deserialization as json
        context2 = ServerContext(**json.loads(context_json))
        self.assertEqual(context2, context)

        # Check roundtrip
        context3 = ServerContext.from_json(context_json)
        self.assertEqual(context3, context)


if __name__ == '__main__':
    unittest.main()
