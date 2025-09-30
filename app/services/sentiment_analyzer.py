from typing import Dict, Tuple
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        self.escalation_threshold = -0.5
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        try:
            textblob_score = self._get_textblob_sentiment(text)
            vader_score = self._get_vader_sentiment(text)
            
            if textblob_score == 0.0 and vader_score == 0.0:
                logger.warning("Both sentiment analyzers failed, using neutral sentiment")
                combined_score = 0.0
            else:
                combined_score = (textblob_score + vader_score) / 2
            
            return {
                "sentiment_score": round(combined_score, 3),
                "textblob_score": round(textblob_score, 3),
                "vader_score": round(vader_score, 3),
                "escalation_required": combined_score < self.escalation_threshold,
                "analysis_successful": not (textblob_score == 0.0 and vader_score == 0.0)
            }
        except Exception as e:
            logger.error(f"Sentiment analysis completely failed: {e}")
            return {
                "sentiment_score": 0.0,
                "textblob_score": 0.0,
                "vader_score": 0.0,
                "escalation_required": False,
                "analysis_successful": False,
                "error": str(e)
            }
    
    def _get_textblob_sentiment(self, text: str) -> float:
        try:
            if not text or not text.strip():
                return 0.0
            
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity is None or not isinstance(polarity, (int, float)):
                logger.warning("TextBlob returned invalid polarity value")
                return 0.0
                
            return float(polarity)
        except ImportError as e:
            logger.error(f"TextBlob import error: {e}")
            return 0.0
        except Exception as e:
            logger.warning(f"TextBlob sentiment analysis failed: {e}")
            return 0.0
    
    def _get_vader_sentiment(self, text: str) -> float:
        try:
            if not text or not text.strip():
                return 0.0
            
            if not hasattr(self, 'vader_analyzer') or self.vader_analyzer is None:
                logger.warning("VADER analyzer not initialized")
                return 0.0
            
            scores = self.vader_analyzer.polarity_scores(text)
            compound = scores.get('compound', 0.0)
            
            if compound is None or not isinstance(compound, (int, float)):
                logger.warning("VADER returned invalid compound score")
                return 0.0
                
            return float(compound)
        except ImportError as e:
            logger.error(f"VADER import error: {e}")
            return 0.0
        except Exception as e:
            logger.warning(f"VADER sentiment analysis failed: {e}")
            return 0.0
    
    def get_sentiment_label(self, score: float) -> str:
        if score >= 0.1:
            return "positive"
        elif score <= -0.1:
            return "negative"
        else:
            return "neutral"
    
    def should_escalate(self, sentiment_score: float) -> bool:
        return sentiment_score < self.escalation_threshold
    
    def get_sentiment_emoji(self, score: float) -> str:
        if score >= 0.1:
            return "😊"
        elif score <= -0.1:
            return "😠"
        else:
            return "😐"