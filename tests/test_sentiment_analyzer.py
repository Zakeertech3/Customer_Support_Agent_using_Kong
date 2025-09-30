import pytest
from app.services.sentiment_analyzer import SentimentAnalyzer

class TestSentimentAnalyzer:
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_positive_sentiment_detection(self):
        positive_texts = [
            "I love this service! It's amazing and works perfectly.",
            "Great job! This is exactly what I needed.",
            "Excellent support, very helpful and friendly.",
            "Thank you so much! This solved my problem completely."
        ]
        
        for text in positive_texts:
            result = self.analyzer.analyze_sentiment(text)
            assert result["sentiment_score"] > 0, f"Expected positive sentiment for: {text}"
            assert self.analyzer.get_sentiment_label(result["sentiment_score"]) == "positive"
            assert self.analyzer.get_sentiment_emoji(result["sentiment_score"]) == "😊"
            assert not result["escalation_required"]
    
    def test_negative_sentiment_detection(self):
        negative_texts = [
            "This is terrible! I hate this service and it never works.",
            "Absolutely awful experience. This is completely broken.",
            "I'm extremely frustrated and angry with this poor service.",
            "This is the worst support I've ever experienced. Unacceptable!"
        ]
        
        for text in negative_texts:
            result = self.analyzer.analyze_sentiment(text)
            assert result["sentiment_score"] < 0, f"Expected negative sentiment for: {text}"
            assert self.analyzer.get_sentiment_label(result["sentiment_score"]) == "negative"
            assert self.analyzer.get_sentiment_emoji(result["sentiment_score"]) == "😠"
    
    def test_neutral_sentiment_detection(self):
        neutral_texts = [
            "What is the status of my order?",
            "I need to update my billing address.",
            "Please provide documentation for the API.",
            "Where can I find the user manual?"
        ]
        
        for text in neutral_texts:
            result = self.analyzer.analyze_sentiment(text)
            sentiment_score = result["sentiment_score"]
            assert -0.3 <= sentiment_score <= 0.3, f"Expected neutral-range sentiment for: {text}"
            
        truly_neutral_text = "The system is operational."
        result = self.analyzer.analyze_sentiment(truly_neutral_text)
        assert self.analyzer.get_sentiment_label(result["sentiment_score"]) in ["neutral", "positive"]
    
    def test_escalation_threshold_detection(self):
        highly_negative_text = "This is absolutely terrible! I'm furious and this service is completely useless!"
        result = self.analyzer.analyze_sentiment(highly_negative_text)
        
        assert result["sentiment_score"] < -0.5
        assert result["escalation_required"] == True
        assert self.analyzer.should_escalate(result["sentiment_score"]) == True
    
    def test_no_escalation_for_mild_negative(self):
        mildly_negative_text = "This could be better, not quite what I expected."
        result = self.analyzer.analyze_sentiment(mildly_negative_text)
        
        if result["sentiment_score"] >= -0.5:
            assert result["escalation_required"] == False
            assert self.analyzer.should_escalate(result["sentiment_score"]) == False
    
    def test_sentiment_score_range(self):
        test_texts = [
            "I absolutely love this amazing service!",
            "This is okay, nothing special.",
            "I hate this terrible service completely!"
        ]
        
        for text in test_texts:
            result = self.analyzer.analyze_sentiment(text)
            assert -1.0 <= result["sentiment_score"] <= 1.0
            assert -1.0 <= result["textblob_score"] <= 1.0
            assert -1.0 <= result["vader_score"] <= 1.0
    
    def test_empty_text_handling(self):
        result = self.analyzer.analyze_sentiment("")
        assert result["sentiment_score"] == 0.0
        assert not result["escalation_required"]
    
    def test_combined_scoring_mechanism(self):
        text = "This service is great but has some issues."
        result = self.analyzer.analyze_sentiment(text)
        
        assert "sentiment_score" in result
        assert "textblob_score" in result
        assert "vader_score" in result
        assert "escalation_required" in result
        
        expected_combined = (result["textblob_score"] + result["vader_score"]) / 2
        assert abs(result["sentiment_score"] - expected_combined) < 0.001