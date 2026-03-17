from deep_translator import GoogleTranslator


class Translator:
    def __init__(self):
        self.translator = GoogleTranslator(source='en', target='zh-CN')

    def translate(self, text: str) -> str:
        """
        Translate English text to Simplified Chinese.
        
        Args:
            text: English text to translate
            
        Returns:
            Translated Chinese text
        """
        if not text or not text.strip():
            return ""
        
        try:
            # Translate using Google Translate
            translated = self.translator.translate(text)
            return translated if translated else ""
        except Exception as e:
            print(f"Translation error: {e}")
            return ""
