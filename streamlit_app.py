import streamlit as st
import json
import requests
from datetime import datetime as dt, timezone
from typing import List, Dict, Any, Optional
import uuid
from collections import Counter

from components.api_client import StreamlitAPIClient
from components.error_handler import ErrorHandler, display_error_message, handle_api_error


def export_session_data():
    if st.session_state.session_created:
        result = st.session_state.api_client.export_session_with_error_handling(st.session_state.session_id)
        
        if not result.get("error"):
            return result
        else:
            st.error(f"Failed to export session: {result.get('message', 'Unknown error')}")
            return None
    return None


def get_live_metrics():
    try:
        result = st.session_state.api_client.get_metrics_with_error_handling()
        
        if not result.get("error"):
            return result
        else:
            return {"error": True, "message": result.get("message", "Failed to fetch metrics")}
    except Exception as e:
        st.warning("⚠️ Metrics temporarily unavailable")
        return {"error": True, "message": f"Metrics service error: {str(e)}"}


def create_manual_escalation(reason: str = "Manual escalation requested"):
    result = st.session_state.api_client.create_manual_escalation_with_error_handling(
        st.session_state.customer_id, 
        reason
    )
    
    if not result.get("error"):
        return result
    else:
        st.error(f"Failed to create escalation: {result.get('message', 'Unknown error')}")
        return None


def get_customer_escalation_history():
    result = st.session_state.api_client.get_escalations_with_error_handling(st.session_state.customer_id)
    
    if not result.get("error"):
        return result
    else:
        return {"escalations": [], "error": True}


def get_performance_dashboard_data():
    result = st.session_state.api_client.get_performance_data_with_error_handling()
    return result


def backup_session_data():
    result = st.session_state.api_client.backup_sessions()
    
    if result.success:
        return result.data
    else:
        st.error(f"Failed to backup sessions: {result.error}")
        return None


def check_api_connectivity():
    result = st.session_state.api_client.health_check()
    
    if result.success:
        return {
            "status": "healthy",
            "data": result.data,
            "connected": True
        }
    else:
        return {
            "status": "unhealthy",
            "error": result.error,
            "error_type": result.error_type,
            "connected": False
        }


def display_api_status():
    connected = ErrorHandler.display_connection_status(st.session_state.api_client)
    
    if connected and st.button("🔍 API Health Details", key="api_health_details_btn"):
        health_data = ErrorHandler.safe_api_call(
            st.session_state.api_client, 
            "health_check", 
            context="API Health Check"
        )
        if health_data:
            with st.expander("API Health Status", expanded=True):
                st.json(health_data)


def get_escalation_dashboard_data():
    escalation_data = get_customer_escalation_history()
    
    if not escalation_data.get("error"):
        return escalation_data
    else:
        return {"escalations": [], "total": 0, "error": True}


def display_escalation_management():
    st.subheader("🚨 Escalation Management")
    
    escalation_data = get_escalation_dashboard_data()
    
    if escalation_data.get("error"):
        st.warning("⚠️ Could not fetch escalation data from backend")
        return
    
    escalations = escalation_data.get("escalations", [])
    
    if not escalations:
        st.info("✅ No escalations for this customer")
        return
    
    st.write(f"**Total Escalations:** {len(escalations)}")
    
    for escalation in escalations[-5:]:
        with st.expander(f"🎫 Ticket {escalation.get('ticket_id', 'N/A')[:8]}... - {escalation.get('reason', 'Unknown')}"):
            st.write(f"**Status:** {escalation.get('status', 'Unknown')}")
            st.write(f"**Priority:** {escalation.get('priority', 'Unknown')}")
            st.write(f"**Created:** {escalation.get('created_at', 'Unknown')}")
            
            if escalation.get("summary"):
                st.write(f"**Summary:** {escalation['summary']}")


def display_session_management():
    st.subheader("📝 Session Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Session Details", key="session_details_btn"):
            session_data = st.session_state.api_client.get_session_with_error_handling(st.session_state.session_id)
            if not session_data.get("error"):
                with st.expander("Session Information", expanded=True):
                    st.json(session_data)
            else:
                st.error(f"Failed to fetch session details: {session_data.get('message', 'Unknown error')}")
    
    with col2:
        if st.button("📊 Session Stats", key="session_stats_btn"):
            stats_data = st.session_state.api_client.get_session_statistics()
            if stats_data.success:
                with st.expander("Session Statistics", expanded=True):
                    st.json(stats_data.data)
            else:
                st.error(f"Failed to fetch session statistics: {stats_data.error}")
    
    with col3:
        if st.button("🧹 Cleanup Old Sessions", key="cleanup_sessions_btn"):
            with st.spinner("Cleaning up old sessions..."):
                cleanup_result = st.session_state.api_client.cleanup_old_sessions(30)
                if cleanup_result.success:
                    deleted_count = cleanup_result.data.get("deleted_sessions", 0)
                    st.success(f"✅ Cleaned up {deleted_count} old sessions")
                else:
                    st.error(f"Failed to cleanup sessions: {cleanup_result.error}")


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "customer_id" not in st.session_state:
        st.session_state.customer_id = f"customer_{str(uuid.uuid4())[:8]}"
    
    if "api_client" not in st.session_state:
        st.session_state.api_client = StreamlitAPIClient()
    
    if "session_created" not in st.session_state:
        st.session_state.session_created = False
    
    if "error_message" not in st.session_state:
        st.session_state.error_message = None


def display_error_message(error_msg: str, error_type: str = "ERROR"):
    if error_type == "CONNECTION_ERROR":
        st.error(f"🔌 Connection Error: {error_msg}")
        st.info("Please ensure the backend API is running on http://localhost:8080")
    elif error_type == "SESSION_ERROR":
        st.error(f"📝 Session Error: {error_msg}")
    elif error_type == "API_ERROR":
        st.error(f"⚠️ API Error: {error_msg}")
    else:
        st.error(f"❌ Error: {error_msg}")


def get_sentiment_indicator(sentiment_score: Optional[float]) -> tuple[str, str, str]:
    if sentiment_score is None:
        return "😐", "neutral", "#6c757d"
    elif sentiment_score > 0.5:
        return "😊", "very positive", "#28a745"
    elif sentiment_score > 0.2:
        return "🙂", "positive", "#90EE90"
    elif sentiment_score > 0.05:
        return "😐", "slightly positive", "#17a2b8"
    elif sentiment_score < -0.5:
        return "😠", "very negative", "#dc3545"
    elif sentiment_score < -0.2:
        return "😕", "negative", "#fd7e14"
    elif sentiment_score < -0.05:
        return "😐", "slightly negative", "#ffc107"
    else:
        return "😐", "neutral", "#6c757d"


def display_escalation_banner(escalation_info: Dict[str, Any]):
    if escalation_info.get("escalated"):
        escalation_reason = escalation_info.get("escalation_reason", "unknown")
        ticket_id = escalation_info.get("ticket_id", "N/A")
        
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #dc3545, #fd7e14);
                color: white;
                padding: 15px;
                border-radius: 10px;
                border-left: 5px solid #dc3545;
                margin: 10px 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h4 style="margin: 0 0 10px 0; color: white;">🚨 ESCALATED TO HUMAN AGENT 🚨</h4>
                <p style="margin: 5px 0; color: white;"><strong>Reason:</strong> {escalation_reason.title()}</p>
                <p style="margin: 5px 0; color: white;"><strong>Ticket ID:</strong> {ticket_id}</p>
                <p style="margin: 5px 0; color: white;"><strong>Status:</strong> 🔥 Priority handling requested</p>
                <hr style="border-color: rgba(255,255,255,0.3); margin: 10px 0;">
                <p style="margin: 0; color: white; font-style: italic;">
                    A human support agent will review this conversation and respond as soon as possible.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


def display_processing_status(status: str):
    status_configs = {
        "analyzing": {"emoji": "🔍", "text": "Analyzing query complexity...", "color": "#17a2b8", "bg": "#e7f3ff"},
        "routing": {"emoji": "🎯", "text": "Routing to optimal model...", "color": "#6f42c1", "bg": "#f3e7ff"},
        "processing": {"emoji": "⚡", "text": "Processing with AI model...", "color": "#fd7e14", "bg": "#fff3e0"},
        "sentiment": {"emoji": "💭", "text": "Analyzing sentiment...", "color": "#20c997", "bg": "#e8f5f0"},
        "caching": {"emoji": "💾", "text": "Checking semantic cache...", "color": "#6c757d", "bg": "#f8f9fa"},
        "complete": {"emoji": "✅", "text": "Response ready", "color": "#28a745", "bg": "#e8f5e8"},
        "escalating": {"emoji": "🚨", "text": "Escalating to human agent...", "color": "#dc3545", "bg": "#ffe6e6"}
    }
    
    config = status_configs.get(status, {"emoji": "⏳", "text": "Processing...", "color": "#6c757d", "bg": "#f8f9fa"})
    
    st.markdown(
        f"""
        <div style="
            background: {config["bg"]};
            color: {config["color"]};
            padding: 8px 12px;
            border-radius: 20px;
            border-left: 3px solid {config["color"]};
            font-size: 14px;
            margin: 8px 0;
            display: inline-block;
            animation: pulse 1.5s infinite;
        ">
            {config["emoji"]} {config["text"]}
        </div>
        <style>
        @keyframes pulse {{
            0% {{ opacity: 0.7; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.7; }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def display_message_metadata(message: Dict[str, Any]):
    metadata_cols = st.columns([2, 2, 2, 2])
    
    with metadata_cols[0]:
        if message.get("sentiment_score") is not None:
            emoji, sentiment_text, color = get_sentiment_indicator(message.get("sentiment_score"))
            sentiment_score = message.get("sentiment_score")
            st.markdown(
                f"""
                <div style="
                    background: {color}15;
                    color: {color};
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    display: inline-block;
                    border: 1px solid {color}40;
                ">
                    {emoji} {sentiment_text} ({sentiment_score:.2f})
                </div>
                """,
                unsafe_allow_html=True
            )
    
    with metadata_cols[1]:
        if message.get("model_used"):
            model_name = message.get("model_used", "").replace("llama-", "").replace("openai/", "")
            model_color = "#6f42c1" if "gpt" in model_name.lower() else "#17a2b8" if "70b" in model_name else "#28a745"
            st.markdown(
                f"""
                <div style="
                    background: {model_color}15;
                    color: {model_color};
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    display: inline-block;
                    border: 1px solid {model_color}40;
                ">
                    🤖 {model_name}
                </div>
                """,
                unsafe_allow_html=True
            )
    
    with metadata_cols[2]:
        if message.get("response_time_ms"):
            response_time = message.get("response_time_ms")
            time_color = "#28a745" if response_time < 500 else "#ffc107" if response_time < 2000 else "#dc3545"
            time_bg = "#28a74515" if response_time < 500 else "#ffc10715" if response_time < 2000 else "#dc354515"
            st.markdown(
                f"""
                <div style="
                    background: {time_bg};
                    color: {time_color};
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    display: inline-block;
                    border: 1px solid {time_color}40;
                ">
                    ⏱️ {response_time}ms
                </div>
                """,
                unsafe_allow_html=True
            )
    
    with metadata_cols[3]:
        indicators = []
        if message.get("cached"):
            indicators.append({"text": "💾 cached", "color": "#6c757d"})
        
        complexity_score = message.get("complexity_score")
        if complexity_score is not None:
            if complexity_score > 0.8:
                indicators.append({"text": "🔥 complex", "color": "#dc3545"})
            elif complexity_score > 0.5:
                indicators.append({"text": "⚡ moderate", "color": "#fd7e14"})
            else:
                indicators.append({"text": "💡 simple", "color": "#28a745"})
        
        for indicator in indicators:
            st.markdown(
                f"""
                <div style="
                    background: {indicator["color"]}15;
                    color: {indicator["color"]};
                    padding: 2px 6px;
                    border-radius: 10px;
                    font-size: 10px;
                    display: inline-block;
                    margin: 1px;
                    border: 1px solid {indicator["color"]}40;
                ">
                    {indicator["text"]}
                </div>
                """,
                unsafe_allow_html=True
            )


def display_escalation_status_panel():
    escalated_messages = [msg for msg in st.session_state.messages if msg.get("escalated")]
    
    if escalated_messages:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #dc3545, #fd7e14);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 15px 0;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            ">
                <h3 style="margin: 0; color: white;">🚨 Active Escalations</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Human agent intervention requested</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        for i, msg in enumerate(escalated_messages):
            escalation_reason = msg.get('escalation_reason', 'Unknown').title()
            ticket_id = msg.get('ticket_id', 'N/A')
            
            with st.expander(
                f"🎫 Ticket #{i+1}: {escalation_reason} - {ticket_id[:8]}...", 
                expanded=i == len(escalated_messages)-1
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**🎫 Ticket ID:** `{ticket_id}`")
                    st.markdown(f"**📋 Reason:** {escalation_reason}")
                    
                    query_preview = msg.get('content', '')[:150]
                    if len(msg.get('content', '')) > 150:
                        query_preview += "..."
                    st.markdown(f"**💬 Query:** {query_preview}")
                    
                    if msg.get("sentiment_score") is not None:
                        emoji, sentiment_text, color = get_sentiment_indicator(msg.get("sentiment_score"))
                        sentiment_score = msg.get("sentiment_score")
                        st.markdown(
                            f"""
                            **😊 Sentiment:** 
                            <span style="
                                background: {color}20;
                                color: {color};
                                padding: 2px 8px;
                                border-radius: 12px;
                                font-size: 12px;
                            ">
                                {emoji} {sentiment_text} ({sentiment_score:.2f})
                            </span>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    if msg.get("complexity_score") is not None:
                        complexity_pct = msg.get("complexity_score") * 100
                        complexity_color = "#dc3545" if complexity_pct > 80 else "#fd7e14" if complexity_pct > 50 else "#28a745"
                        st.markdown(
                            f"""
                            **🧠 Complexity:** 
                            <span style="
                                background: {complexity_color}20;
                                color: {complexity_color};
                                padding: 2px 8px;
                                border-radius: 12px;
                                font-size: 12px;
                            ">
                                {complexity_pct:.1f}%
                            </span>
                            """,
                            unsafe_allow_html=True
                        )
                
                with col2:
                    st.markdown("**📊 Status**")
                    st.markdown("🔴 **Open**")
                    st.markdown("🔥 **High Priority**")
                    
                    timestamp = msg.get('timestamp', '')
                    if timestamp:
                        try:
                            parsed_dt = dt.fromisoformat(timestamp.replace("Z", "+00:00"))
                            time_str = parsed_dt.strftime("%H:%M:%S")
                            st.caption(f"⏰ {time_str}")
                        except:
                            st.caption(f"⏰ {timestamp}")
                        
                st.markdown(
                    """
                    <div style="
                        background: #e3f2fd;
                        border-left: 4px solid #2196f3;
                        padding: 10px;
                        margin: 10px 0;
                        border-radius: 5px;
                    ">
                        <strong>💡 Next Steps:</strong> A human support agent will review this conversation 
                        and respond as soon as possible. You will be notified when an agent is assigned.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        return True
    return False


def display_message(message: Dict[str, Any], is_user: bool = False):
    role = "user" if is_user else "assistant"
    
    with st.chat_message(role):
        if message.get("escalated") and not is_user:
            display_escalation_banner(message)
        
        st.write(message.get("content", ""))
        
        if not is_user:
            display_message_metadata(message)


def create_session_if_needed():
    if not st.session_state.session_created:
        with st.spinner("Initializing session..."):
            result = st.session_state.api_client.create_session_with_error_handling(
                st.session_state.customer_id, 
                st.session_state.session_id
            )
            
            if result.get("error"):
                display_error_message(result.get("message", "Unknown error"), result.get("error_type", "ERROR"))
                return False
            else:
                st.session_state.session_created = True
                return True
    return True


def load_conversation_history():
    if st.session_state.session_created and not st.session_state.messages:
        with st.spinner("Loading conversation history..."):
            result = st.session_state.api_client.get_session_with_error_handling(st.session_state.session_id)
            
            if not result.get("error"):
                session_data = result.get("session", {})
                if session_data.get("messages"):
                    st.session_state.messages = session_data["messages"]


def generate_metrics_export(assistant_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not assistant_messages:
        return {"error": "No data available"}
    
    response_times = [msg.get("response_time_ms", 0) for msg in assistant_messages]
    sentiment_scores = [msg.get("sentiment_score") for msg in assistant_messages if msg.get("sentiment_score") is not None]
    complexity_scores = [msg.get("complexity_score") for msg in assistant_messages if msg.get("complexity_score") is not None]
    models_used = [msg.get("model_used") for msg in assistant_messages if msg.get("model_used")]
    
    model_counts = Counter(models_used)
    cached_responses = sum(1 for msg in assistant_messages if msg.get("cached"))
    escalated_count = len([msg for msg in st.session_state.messages if msg.get("escalated")])
    
    total_tokens = sum(msg.get("tokens_used", 0) for msg in assistant_messages)
    total_cost = 0
    for msg in assistant_messages:
        model = msg.get("model_used", "")
        tokens = msg.get("tokens_used", 0)
        if model and tokens:
            total_cost += calculate_cost_estimate(model, tokens)
    
    return {
        "export_timestamp": dt.now(timezone.utc).isoformat(),
        "session_id": st.session_state.session_id,
        "customer_id": st.session_state.customer_id,
        "summary": {
            "total_queries": len(assistant_messages),
            "total_messages": len(st.session_state.messages),
            "escalated_queries": escalated_count,
            "cache_hits": cached_responses,
            "unique_models_used": len(set(models_used))
        },
        "performance": {
            "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
            "min_response_time_ms": min(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "cache_hit_rate_percent": (cached_responses / len(assistant_messages)) * 100 if assistant_messages else 0,
            "escalation_rate_percent": (escalated_count / len(assistant_messages)) * 100 if assistant_messages else 0
        },
        "model_usage": {
            "distribution": dict(model_counts),
            "total_tokens": total_tokens,
            "estimated_total_cost": total_cost,
            "avg_tokens_per_query": total_tokens / len(assistant_messages) if assistant_messages else 0
        },
        "sentiment_analysis": {
            "avg_sentiment": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else None,
            "min_sentiment": min(sentiment_scores) if sentiment_scores else None,
            "max_sentiment": max(sentiment_scores) if sentiment_scores else None,
            "positive_count": sum(1 for score in sentiment_scores if score > 0.1),
            "neutral_count": sum(1 for score in sentiment_scores if -0.1 <= score <= 0.1),
            "negative_count": sum(1 for score in sentiment_scores if score < -0.1)
        },
        "complexity_analysis": {
            "avg_complexity": sum(complexity_scores) / len(complexity_scores) if complexity_scores else None,
            "high_complexity_queries": sum(1 for score in complexity_scores if score > 0.8),
            "medium_complexity_queries": sum(1 for score in complexity_scores if 0.3 <= score <= 0.8),
            "low_complexity_queries": sum(1 for score in complexity_scores if score < 0.3)
        }
    }


def calculate_cost_estimate(model_name: str, tokens: int) -> float:
    cost_per_1k_tokens = {
        "llama-3.3-70b-versatile": 0.00059,
        "openai/gpt-oss-120b": 0.0015,
        "llama-3.1-8b-instant": 0.00005
    }
    
    base_model = model_name.replace("llama-", "").replace("openai/", "")
    if "70b" in base_model:
        rate = cost_per_1k_tokens["llama-3.3-70b-versatile"]
    elif "120b" in base_model:
        rate = cost_per_1k_tokens["openai/gpt-oss-120b"]
    elif "8b" in base_model:
        rate = cost_per_1k_tokens["llama-3.1-8b-instant"]
    else:
        rate = cost_per_1k_tokens.get(model_name, 0.001)
    
    return (tokens / 1000) * rate


def display_metrics_dashboard(location="main"):
    st.header("📊 Live Metrics Dashboard")
    
    metrics_col1, metrics_col2, metrics_col3 = st.columns([2, 1, 1])
    
    with metrics_col1:
        if st.button("🔄 Refresh Metrics", help="Click to update metrics in real-time", key=f"refresh_metrics_btn_{location}"):
            st.rerun()
    
    with metrics_col2:
        if st.button("📊 Export Metrics", help="Download metrics as JSON", key=f"export_metrics_btn_{location}"):
            assistant_messages = [msg for msg in st.session_state.messages if msg.get("role") == "assistant" and not msg.get("error")]
            metrics_data = generate_metrics_export(assistant_messages)
            st.download_button(
                label="💾 Download JSON",
                data=json.dumps(metrics_data, indent=2),
                file_name=f"metrics_{dt.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key=f"download_metrics_json_{location}"
            )
    
    with metrics_col3:
        if st.button("🌐 Live API Metrics", help="Fetch live metrics from backend", key=f"live_api_metrics_btn_{location}"):
            with st.spinner("Fetching live metrics..."):
                live_metrics = get_live_metrics()
                if not live_metrics.get("error"):
                    st.success("✅ Live metrics loaded!")
                    with st.expander("🔍 Backend Metrics", expanded=True):
                        st.json(live_metrics)
                else:
                    st.warning("⚠️ Could not fetch live metrics from backend")
    
    assistant_messages = [msg for msg in st.session_state.messages if msg.get("role") == "assistant" and not msg.get("error")]
    
    if not assistant_messages:
        st.info("💡 Metrics will appear after your first query")
        return
    
    st.caption(f"📈 Live data from {len(assistant_messages)} responses • Last updated: {dt.now().strftime('%H:%M:%S')}")
    
    if len(assistant_messages) >= 2:
        recent_messages = assistant_messages[-3:] if len(assistant_messages) >= 3 else assistant_messages[-2:]
        older_messages = assistant_messages[:-3] if len(assistant_messages) >= 3 else assistant_messages[:-2]
        
        if older_messages:
            recent_avg_time = sum(msg.get("response_time_ms", 0) for msg in recent_messages) / len(recent_messages)
            older_avg_time = sum(msg.get("response_time_ms", 0) for msg in older_messages) / len(older_messages)
            
            time_trend = "📈" if recent_avg_time > older_avg_time else "📉"
            trend_text = "improving" if recent_avg_time < older_avg_time else "slower"
            
            st.caption(f"{time_trend} Response time trend: {trend_text} (recent: {recent_avg_time:.0f}ms vs previous: {older_avg_time:.0f}ms)")
    
    st.subheader("⚡ Performance Metrics")
    
    perf_col1, perf_col2, perf_col3 = st.columns(3)
    
    response_times = [msg.get("response_time_ms", 0) for msg in assistant_messages]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    min_response_time = min(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0
    
    with perf_col1:
        color = "normal"
        if avg_response_time < 500:
            color = "normal"
        elif avg_response_time < 2000:
            color = "off"
        else:
            color = "inverse"
        
        st.metric(
            "Avg Response Time", 
            f"{avg_response_time:.0f}ms",
            delta=f"Range: {min_response_time:.0f}-{max_response_time:.0f}ms",
            delta_color=color
        )
    
    with perf_col2:
        cached_responses = sum(1 for msg in assistant_messages if msg.get("cached"))
        cache_hit_rate = (cached_responses / len(assistant_messages)) * 100 if assistant_messages else 0
        
        cache_color = "normal" if cache_hit_rate > 20 else "off"
        st.metric(
            "Cache Hit Rate", 
            f"{cache_hit_rate:.1f}%",
            delta=f"{cached_responses}/{len(assistant_messages)} hits",
            delta_color=cache_color
        )
    
    with perf_col3:
        escalated_count = len([msg for msg in st.session_state.messages if msg.get("escalated")])
        escalation_rate = (escalated_count / len(assistant_messages)) * 100 if assistant_messages else 0
        
        escalation_color = "inverse" if escalation_rate > 20 else "off" if escalation_rate > 10 else "normal"
        st.metric(
            "Escalation Rate", 
            f"{escalation_rate:.1f}%",
            delta=f"{escalated_count} escalated",
            delta_color=escalation_color
        )
    
    st.subheader("🤖 Model Usage Analytics")
    
    models_used = [msg.get("model_used") for msg in assistant_messages if msg.get("model_used")]
    if models_used:
        from collections import Counter
        model_counts = Counter(models_used)
        
        model_col1, model_col2 = st.columns(2)
        
        with model_col1:
            st.write("**Model Distribution:**")
            for model, count in model_counts.most_common():
                percentage = (count / len(models_used)) * 100
                model_display = model.replace("llama-", "").replace("openai/", "")
                st.write(f"• {model_display}: {count} ({percentage:.1f}%)")
        
        with model_col2:
            model_response_times = {}
            for msg in assistant_messages:
                model = msg.get("model_used")
                response_time = msg.get("response_time_ms", 0)
                if model and response_time:
                    if model not in model_response_times:
                        model_response_times[model] = []
                    model_response_times[model].append(response_time)
            
            st.write("**Avg Response Time by Model:**")
            for model, times in model_response_times.items():
                avg_time = sum(times) / len(times)
                model_display = model.replace("llama-", "").replace("openai/", "")
                color = "🟢" if avg_time < 1000 else "🟡" if avg_time < 3000 else "🔴"
                st.write(f"• {color} {model_display}: {avg_time:.0f}ms")
    
    st.subheader("💰 Cost Analysis")
    
    cost_col1, cost_col2, cost_col3 = st.columns(3)
    
    total_tokens = sum(msg.get("tokens_used", 0) for msg in assistant_messages)
    total_cost = 0
    
    for msg in assistant_messages:
        model = msg.get("model_used", "")
        tokens = msg.get("tokens_used", 0)
        if model and tokens:
            total_cost += calculate_cost_estimate(model, tokens)
    
    with cost_col1:
        st.metric("Total Tokens", f"{total_tokens:,}")
    
    with cost_col2:
        st.metric("Estimated Cost", f"${total_cost:.4f}")
    
    with cost_col3:
        avg_tokens_per_query = total_tokens / len(assistant_messages) if assistant_messages else 0
        st.metric("Avg Tokens/Query", f"{avg_tokens_per_query:.0f}")
    
    if models_used:
        st.write("**Cost Breakdown by Model:**")
        model_costs = {}
        for msg in assistant_messages:
            model = msg.get("model_used", "")
            tokens = msg.get("tokens_used", 0)
            if model and tokens:
                cost = calculate_cost_estimate(model, tokens)
                if model not in model_costs:
                    model_costs[model] = {"cost": 0, "tokens": 0, "queries": 0}
                model_costs[model]["cost"] += cost
                model_costs[model]["tokens"] += tokens
                model_costs[model]["queries"] += 1
        
        for model, data in sorted(model_costs.items(), key=lambda x: x[1]["cost"], reverse=True):
            model_display = model.replace("llama-", "").replace("openai/", "")
            cost_per_query = data["cost"] / data["queries"]
            st.write(f"• {model_display}: ${data['cost']:.4f} ({data['queries']} queries, ${cost_per_query:.4f}/query)")
    
    st.subheader("😊 Sentiment Analytics")
    
    sentiment_col1, sentiment_col2 = st.columns(2)
    
    sentiment_scores = [msg.get("sentiment_score") for msg in assistant_messages if msg.get("sentiment_score") is not None]
    
    with sentiment_col1:
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            emoji, sentiment_text, color = get_sentiment_indicator(avg_sentiment)
            
            st.metric("Average Sentiment", f"{emoji} {sentiment_text}")
            
            positive_count = sum(1 for score in sentiment_scores if score > 0.1)
            neutral_count = sum(1 for score in sentiment_scores if -0.1 <= score <= 0.1)
            negative_count = sum(1 for score in sentiment_scores if score < -0.1)
            
            st.write("**Sentiment Distribution:**")
            st.write(f"• 😊 Positive: {positive_count} ({(positive_count/len(sentiment_scores)*100):.1f}%)")
            st.write(f"• 😐 Neutral: {neutral_count} ({(neutral_count/len(sentiment_scores)*100):.1f}%)")
            st.write(f"• 😠 Negative: {negative_count} ({(negative_count/len(sentiment_scores)*100):.1f}%)")
    
    with sentiment_col2:
        if sentiment_scores:
            min_sentiment = min(sentiment_scores)
            max_sentiment = max(sentiment_scores)
            
            st.metric("Sentiment Range", f"{min_sentiment:.2f} to {max_sentiment:.2f}")
            
            negative_escalations = len([msg for msg in st.session_state.messages 
                                     if msg.get("escalated") and msg.get("escalation_reason") == "sentiment"])
            
            if negative_escalations > 0:
                st.warning(f"⚠️ {negative_escalations} sentiment-based escalations")
            else:
                st.success("✅ No negative sentiment escalations")
    
    st.subheader("🔄 Real-time Session Stats")
    
    session_col1, session_col2, session_col3 = st.columns(3)
    
    with session_col1:
        total_messages = len(st.session_state.messages)
        user_messages = len([msg for msg in st.session_state.messages if msg.get("role") == "user"])
        st.metric("Total Messages", total_messages, delta=f"{user_messages} from user")
    
    with session_col2:
        if assistant_messages:
            session_duration = "Active"
            first_message = min(assistant_messages, key=lambda x: x.get("timestamp", ""))
            if first_message.get("timestamp"):
                try:
                    start_time = dt.fromisoformat(first_message["timestamp"].replace("Z", "+00:00"))
                    duration = dt.now(timezone.utc) - start_time.replace(tzinfo=None)
                    session_duration = f"{duration.seconds // 60}m {duration.seconds % 60}s"
                except:
                    session_duration = "Active"
            
            st.metric("Session Duration", session_duration)
    
    with session_col3:
        complexity_scores = [msg.get("complexity_score") for msg in assistant_messages if msg.get("complexity_score") is not None]
        if complexity_scores:
            avg_complexity = sum(complexity_scores) / len(complexity_scores)
            complexity_pct = avg_complexity * 100
            
            complexity_color = "inverse" if avg_complexity > 0.8 else "off" if avg_complexity > 0.5 else "normal"
            st.metric("Avg Query Complexity", f"{complexity_pct:.1f}%", delta_color=complexity_color)


def main():
    # Initialize session state FIRST before anything else
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "customer_id" not in st.session_state:
        st.session_state.customer_id = f"customer_{str(uuid.uuid4())[:8]}"
    if "api_client" not in st.session_state:
        st.session_state.api_client = StreamlitAPIClient()
    if "session_created" not in st.session_state:
        st.session_state.session_created = False
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    
    st.set_page_config(
        page_title="Customer Support Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    escalated_count = len([msg for msg in st.session_state.messages if msg.get("escalated")])
    
    if escalated_count > 0:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #dc3545, #fd7e14);
                color: white;
                padding: 10px 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h1 style="margin: 0; color: white;">🤖 Customer Support Agent 🚨</h1>
                <p style="margin: 5px 0 0 0; color: white; opacity: 0.9;">
                    <strong>{escalated_count} escalation(s) active</strong> - Human agent intervention requested
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.title("🤖 Customer Support Agent")
        st.caption("Intelligent customer support powered by Kong AI Gateway")
    
    if display_escalation_status_panel():
        st.divider()
    
    if not create_session_if_needed():
        st.stop()
    
    load_conversation_history()
    
    if st.session_state.error_message:
        display_error_message(st.session_state.error_message)
        st.session_state.error_message = None
    
    for message in st.session_state.messages:
        if message.get("role") == "user":
            display_message(message, is_user=True)
        else:
            display_message(message, is_user=False)
    
    if prompt := st.chat_input("How can I help you today?"):
        user_message = {
            "id": str(uuid.uuid4()),
            "timestamp": dt.now(timezone.utc).isoformat(),
            "role": "user",
            "content": prompt
        }
        
        st.session_state.messages.append(user_message)
        
        # Process the query and get response
        status_placeholder = st.empty()
        response_placeholder = st.empty()
        
        processing_stages = ["analyzing", "routing", "processing", "sentiment", "complete"]
        
        for i, stage in enumerate(processing_stages[:-1]):
            with status_placeholder:
                display_processing_status(stage)
            
            if i < len(processing_stages) - 2:
                import time
                time.sleep(0.3)
        
        try:
            result = st.session_state.api_client.query_with_error_handling(
                prompt, 
                st.session_state.session_id, 
                st.session_state.customer_id
            )
            
            if result.get("escalated"):
                with status_placeholder:
                    display_processing_status("escalating")
                import time
                time.sleep(0.8)
            
            with status_placeholder:
                display_processing_status("complete")
            
            import time
            time.sleep(0.5)
            status_placeholder.empty()
            
            if result.get("error"):
                error_msg = result.get("message", "Unknown error occurred")
                error_type = result.get("error_type", "API_ERROR")
                fallback_used = result.get("fallback_used", False)
                
                with response_placeholder:
                    ErrorHandler.display_error({
                        "error_type": error_type,
                        "message": error_msg,
                        "fallback_used": fallback_used
                    }, "Query Processing")
                
                fallback_response = "I apologize for the technical difficulties. "
                if error_type == "KONG_GATEWAY_ERROR":
                    fallback_response += "I'm currently using a backup connection to assist you."
                elif error_type == "LLM_API_ERROR":
                    fallback_response += "I'm experiencing issues with my AI models, but I'm still here to help."
                elif error_type == "CONNECTION_ERROR":
                    fallback_response += "I'm having connectivity issues. Please try again in a moment."
                else:
                    fallback_response += "Please try rephrasing your question or contact support if the issue persists."
                
                # Estimate tokens for fallback response
                estimated_tokens = max(30, len(fallback_response) // 4)
                
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "timestamp": dt.now(timezone.utc).isoformat(),
                    "role": "assistant",
                    "content": fallback_response,
                    "model_used": "llama-3.1-8b-instant",  # Fallback model
                    "tokens_used": estimated_tokens,
                    "error": True,
                    "error_type": error_type,
                    "fallback_used": fallback_used
                }
            else:
                # Estimate tokens based on content length (rough approximation: 1 token ≈ 4 characters)
                content = result.get("response", "I'm sorry, I couldn't process your request.")
                estimated_tokens = max(50, len(content) // 4)  # Minimum 50 tokens
                
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "timestamp": dt.now(timezone.utc).isoformat(),
                    "role": "assistant",
                    "content": content,
                    "model_used": result.get("model_used", "llama-3.3-70b-versatile"),
                    "tokens_used": estimated_tokens,
                    "sentiment_score": result.get("sentiment_score"),
                    "complexity_score": result.get("complexity_score"),
                    "response_time_ms": result.get("response_time_ms"),
                    "escalated": result.get("escalated", False),
                    "escalation_reason": result.get("escalation_reason"),
                    "ticket_id": result.get("ticket_id"),
                    "cached": result.get("cached", False)
                }
                
                with response_placeholder:
                    if assistant_message.get("escalated"):
                        display_escalation_banner(assistant_message)
                    st.write(assistant_message["content"])
                    display_message_metadata(assistant_message)
                
        except Exception as e:
            status_placeholder.empty()
            with response_placeholder:
                st.error("❌ Unexpected error occurred while processing your query")
                st.warning("🔄 Please try again or contact support if the issue persists")
            
            error_content = "I encountered an unexpected error while processing your request. Please try again."
            estimated_tokens = max(25, len(error_content) // 4)
            
            assistant_message = {
                "id": str(uuid.uuid4()),
                "timestamp": dt.now(timezone.utc).isoformat(),
                "role": "assistant",
                "content": error_content,
                "model_used": "llama-3.1-8b-instant",  # Fallback model
                "tokens_used": estimated_tokens,
                "error": True,
                "error_type": "UNEXPECTED_ERROR"
            }
        
        # Add the assistant message to session state
        st.session_state.messages.append(assistant_message)
        
        # Force a rerun to show the updated conversation
        st.rerun()
    
    with st.sidebar:
        st.header("Session Info")
        st.write(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
        st.write(f"**Customer ID:** `{st.session_state.customer_id}`")
        st.write(f"**Messages:** {len(st.session_state.messages)}")
        
        assistant_messages = [msg for msg in st.session_state.messages if msg.get("role") == "assistant" and not msg.get("error")]
        if assistant_messages:
            st.subheader("⚡ Quick Stats")
            
            quick_col1, quick_col2 = st.columns(2)
            
            with quick_col1:
                avg_response_time = sum(msg.get("response_time_ms", 0) for msg in assistant_messages) / len(assistant_messages)
                time_color = "🟢" if avg_response_time < 1000 else "🟡" if avg_response_time < 3000 else "🔴"
                st.metric("Avg Response", f"{time_color} {avg_response_time:.0f}ms")
                
                cached_responses = sum(1 for msg in assistant_messages if msg.get("cached"))
                cache_rate = (cached_responses / len(assistant_messages)) * 100
                cache_color = "🟢" if cache_rate > 20 else "🟡" if cache_rate > 10 else "🔴"
                st.metric("Cache Rate", f"{cache_color} {cache_rate:.0f}%")
            
            with quick_col2:
                escalated_count = len([msg for msg in st.session_state.messages if msg.get("escalated")])
                escalation_rate = (escalated_count / len(assistant_messages)) * 100 if assistant_messages else 0
                escalation_color = "🔴" if escalation_rate > 20 else "🟡" if escalation_rate > 10 else "🟢"
                st.metric("Escalations", f"{escalation_color} {escalated_count}")
                
                total_cost = 0
                for msg in assistant_messages:
                    model = msg.get("model_used", "")
                    tokens = msg.get("tokens_used", 0)
                    if model and tokens:
                        total_cost += calculate_cost_estimate(model, tokens)
                
                cost_color = "🔴" if total_cost > 0.01 else "🟡" if total_cost > 0.005 else "🟢"
                st.metric("Est. Cost", f"{cost_color} ${total_cost:.4f}")
        
        escalated_messages = [msg for msg in st.session_state.messages if msg.get("escalated")]
        if escalated_messages:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #dc3545, #fd7e14);
                    color: white;
                    padding: 12px;
                    border-radius: 8px;
                    margin: 10px 0;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <strong>🚨 {len(escalated_messages)} ESCALATED</strong>
                </div>
                """,
                unsafe_allow_html=True
            )
            for msg in escalated_messages[-3:]:
                ticket_id = msg.get('ticket_id', 'N/A')[:8]
                reason = msg.get('escalation_reason', 'Unknown').title()
                with st.expander(f"🎫 {ticket_id}... - {reason}"):
                    query_preview = msg.get('content', '')[:80]
                    if len(msg.get('content', '')) > 80:
                        query_preview += "..."
                    st.write(f"**Query:** {query_preview}")
                    
                    if msg.get("sentiment_score") is not None:
                        emoji, sentiment_text, color = get_sentiment_indicator(msg.get("sentiment_score"))
                        st.write(f"**Sentiment:** {emoji} {sentiment_text}")
                    
                    timestamp = msg.get('timestamp', '')
                    if timestamp:
                        try:
                            parsed_dt = dt.fromisoformat(timestamp.replace("Z", "+00:00"))
                            time_str = parsed_dt.strftime("%H:%M")
                            st.caption(f"⏰ {time_str}")
                        except:
                            st.caption(f"⏰ {timestamp}")
                        
        if st.button(" New Session", key="new_session_btn"):
            st.rerun()
        
        if st.button("🗑️ Clear Chat", key="clear_chat_btn"):
            st.session_state.messages = []
            st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Export Session", key="export_session_btn"):
                with st.spinner("Exporting session data..."):
                    export_data = export_session_data()
                    if export_data:
                        st.download_button(
                            label="💾 Download JSON",
                            data=json.dumps(export_data, indent=2),
                            file_name=f"session_{st.session_state.session_id[:8]}_{dt.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key="download_session_json"
                        )
                        st.success("✅ Session exported successfully!")
        
        with col2:
            if st.button("🚨 Manual Escalation", key="manual_escalation_btn"):
                with st.spinner("Creating escalation..."):
                    escalation_result = create_manual_escalation("Manual escalation requested by user")
                    if escalation_result:
                        st.success("✅ Escalation created!")
                        st.rerun()
        
        if st.button("💾 Backup Sessions", key="backup_sessions_btn"):
            with st.spinner("Backing up sessions..."):
                backup_result = backup_session_data()
                if backup_result:
                    st.success("✅ Sessions backed up successfully!")
        
        st.divider()
        
        st.divider()
        
        with st.expander("🔧 API & System Status"):
            display_api_status()
        
        with st.expander("🚨 Escalation Management"):
            display_escalation_management()
        
        with st.expander("📝 Advanced Session Management"):
            display_session_management()
        
        st.session_state.metrics_container = st.container()
        with st.session_state.metrics_container:
            display_metrics_dashboard("sidebar")
        
        st.divider()
        
        st.header("Connection Status")
        try:
            health_response = requests.get("http://localhost:8080/health", timeout=5)
            if health_response.status_code == 200:
                st.success("✅ Backend Connected")
                health_data = health_response.json()
                st.caption(f"Version: {health_data.get('version', 'Unknown')}")
            else:
                st.error("❌ Backend Error")
        except requests.exceptions.RequestException:
            st.error("❌ Backend Offline")
            st.caption("Start the backend with: `python main.py`")


if __name__ == "__main__":
    main()