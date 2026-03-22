"""
Forecast Insights Agent - Answers questions about forecast results
Provides intelligent analysis of forecasting data
"""

from typing import Dict, Any, List
import os
from langchain_community.llms import Ollama

class ForecastInsightsAgent:
    """Agent for answering questions about forecast results."""
    
    def __init__(self):
        """Initialize the insights agent with LLM."""
        self.llm = Ollama(
            model=os.getenv('LLM_MODEL', 'deepseek-r1:14b'),
            base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            timeout=60
        )
    
    def analyze_forecast_results(self, forecast_data: Dict[str, Any], user_question: str) -> Dict[str, Any]:
        """
        Analyze forecast results and answer user questions.
        
        Args:
            forecast_data: The forecast results from ML models
            user_question: User's question about the forecast
            
        Returns:
            Dict with answer, insights, and confidence
        """
        # Extract key metrics from forecast
        context = self._build_forecast_context(forecast_data)
        
        # Create specialized prompt
        prompt = f"""You are an expert automotive market analyst specializing in forecast interpretation.

FORECAST DATA SUMMARY:
{context}

USER QUESTION: {user_question}

Provide a comprehensive answer considering:
1. The specific metrics in the forecast data
2. Growth trends and patterns
3. Model accuracy and confidence levels
4. Key turning points or inflection points
5. Actionable insights for decision-makers

Answer clearly and cite specific numbers from the forecast data.

Answer:"""

        # Get response from LLM
        response = self.llm.invoke(prompt)
        
        # Extract insights
        insights = self._extract_insights(forecast_data)
        
        return {
            'answer': response,
            'question': user_question,
            'insights': insights,
            'forecast_summary': self._get_forecast_summary(forecast_data),
            'confidence': self._calculate_confidence(forecast_data)
        }
    
    def _build_forecast_context(self, forecast_data: Dict[str, Any]) -> str:
        """Build context string from forecast data."""
        context_parts = []
        
        # Model information
        if 'best_model' in forecast_data:
            context_parts.append(f"Best Model: {forecast_data['best_model']}")
        
        if 'best_r2_score' in forecast_data:
            context_parts.append(f"Model Accuracy (R²): {forecast_data['best_r2_score']:.4f}")
        
        # Data quality
        if 'data_quality' in forecast_data:
            quality = forecast_data['data_quality']
            context_parts.append(f"Data Quality Score: {quality.get('quality_score', 'N/A')}")
            context_parts.append(f"Trend Direction: {quality.get('trend_direction', 'N/A')}")
        
        # Forecast values
        if 'models_comparison' in forecast_data:
            comparison = forecast_data['models_comparison']
            
            if 'ensemble' in comparison:
                ensemble = comparison['ensemble']
                forecast_points = ensemble.get('forecast_data', [])
                
                if forecast_points and len(forecast_points) > 0:
                    first_point = forecast_points[0]
                    last_point = forecast_points[-1]
                    
                    context_parts.append(f"\nForecast Period: {len(forecast_points)} periods")
                    context_parts.append(f"Starting Forecast: {first_point.get('forecast', 'N/A')}")
                    context_parts.append(f"Ending Forecast: {last_point.get('forecast', 'N/A')}")
                    
                    # Calculate growth
                    if isinstance(first_point.get('forecast'), (int, float)) and isinstance(last_point.get('forecast'), (int, float)):
                        growth = ((last_point['forecast'] - first_point['forecast']) / first_point['forecast']) * 100
                        context_parts.append(f"Total Growth: {growth:.2f}%")
        
        return "\n".join(context_parts)
    
    def _extract_insights(self, forecast_data: Dict[str, Any]) -> List[str]:
        """Extract key insights from forecast data."""
        insights = []
        
        # Model performance insight
        if 'best_r2_score' in forecast_data:
            r2 = forecast_data['best_r2_score']
            if r2 > 0.8:
                insights.append(f"✅ Excellent model accuracy (R² = {r2:.2f}) - High confidence in predictions")
            elif r2 > 0.6:
                insights.append(f"✓ Good model accuracy (R² = {r2:.2f}) - Reliable predictions")
            else:
                insights.append(f"⚠ Moderate accuracy (R² = {r2:.2f}) - Use predictions with caution")
        
        # Data quality insight
        if 'data_quality' in forecast_data:
            quality_score = forecast_data['data_quality'].get('quality_score')
            if quality_score and quality_score > 0.7:
                insights.append(f"📊 High-quality data (Score: {quality_score:.2f}) - Strong foundation for forecasting")
        
        # Trend insight
        if 'data_quality' in forecast_data:
            trend = forecast_data['data_quality'].get('trend_direction')
            if trend:
                insights.append(f"📈 Market trend: {trend.capitalize()}")
        
        return insights
    
    def _get_forecast_summary(self, forecast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary statistics from forecast."""
        summary = {}
        
        if 'models_comparison' in forecast_data and 'ensemble' in forecast_data['models_comparison']:
            forecast_points = forecast_data['models_comparison']['ensemble'].get('forecast_data', [])
            
            if forecast_points:
                values = [p.get('forecast', 0) for p in forecast_points if isinstance(p.get('forecast'), (int, float))]
                
                if values:
                    summary['min_forecast'] = min(values)
                    summary['max_forecast'] = max(values)
                    summary['avg_forecast'] = sum(values) / len(values)
                    summary['total_periods'] = len(values)
        
        return summary
    
    def _calculate_confidence(self, forecast_data: Dict[str, Any]) -> str:
        """Calculate confidence level based on metrics."""
        r2_score = forecast_data.get('best_r2_score', 0)
        quality_score = forecast_data.get('data_quality', {}).get('quality_score', 0)
        
        avg_score = (r2_score + quality_score) / 2
        
        if avg_score > 0.8:
            return "High"
        elif avg_score > 0.6:
            return "Medium"
        else:
            return "Low"
