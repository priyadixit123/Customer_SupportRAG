
import { useState, useRef, useEffect } from "react";
import "./App.css";
import LandingPage from "./LandingPage";

export default function TravelAgent() {
  // =========================================================
  // AGENT STATE
  // small -> large -> chat
  // =========================================================
  const [agentState, setAgentState] = useState("chat");

  // =========================================================
  // CHAT STATE
  // =========================================================
  const [message, setMessage] = useState("");

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello! 👋 How can I help you with your HolidayBreakz trip?",
    },
  ]);

  // =========================================================
  // VOICE
  // =========================================================
  const [listening, setListening] = useState(false);

  // =========================================================
  // LOADING
  // =========================================================
  const [loading, setLoading] = useState(false);

  // =========================================================
  // SESSION
  // =========================================================
  const [sessionId] = useState(() => {
    try {
      return crypto.randomUUID();
    } catch {
      return `session-${Date.now()}`;
    }
  });

  // =========================================================
  // CHAT BODY REF
  // =========================================================
  const chatBodyRef = useRef(null);

  // =========================================================
  // AUTO SCROLL
  // =========================================================
  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop =
        chatBodyRef.current.scrollHeight;
    }
  }, [messages, loading]);

  // =========================================================
  // AGENT CLICK
  // =========================================================
  function handleAgentClick() {
    if (agentState === "small") {
      setAgentState("large");
      return;
    }

    if (agentState === "large") {
      setAgentState("chat");
      return;
    }
  }

  // =========================================================
  // CLOSE AGENT
  // =========================================================
  function closeAgent() {
    setAgentState("small");
  }

  // =========================================================
  // EXTRACT AI RESPONSE
  // =========================================================
  function extractAIResponse(data) {
    console.log("=================================");
    console.log("BACKEND RESPONSE:");
    console.log(data);
    console.log("=================================");

    if (typeof data?.answer === "string") {
      return data.answer.trim();
    }

    if (typeof data?.response === "string") {
      return data.response.trim();
    }

    console.warn(
      "Could not find AI answer in backend response:",
      data
    );

    return "Sorry, I could not understand the response.";
  }

  // =========================================================
  // SEND MESSAGE
  // =========================================================
  async function sendMessage(text = message) {
    if (!text || !text.trim()) {
      return;
    }

    const userMessage = text.trim();

    console.log("=================================");
    console.log("SENDING MESSAGE:", userMessage);
    console.log("SESSION ID:", sessionId);
    console.log("=================================");

    // -------------------------------------------------------
    // ADD USER MESSAGE
    // -------------------------------------------------------
    setMessages((previousMessages) => [
      ...previousMessages,
      {
        role: "user",
        text: userMessage,
      },
    ]);

    // Clear input
    setMessage("");

    // Start loading
    setLoading(true);

    try {
      // -----------------------------------------------------
      // BACKEND REQUEST
      // -----------------------------------------------------
      const result = await fetch(
        "http://127.0.0.1:8000/chat",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            message: userMessage,
            session_id: sessionId,
          }),
        }
      );

      console.log("BACKEND STATUS:", result.status);

      // -----------------------------------------------------
      // READ RESPONSE
      // -----------------------------------------------------
      const rawResponse = await result.text();

      console.log("RAW BACKEND RESPONSE:");
      console.log(rawResponse);

      // -----------------------------------------------------
      // HTTP ERROR
      // -----------------------------------------------------
      if (!result.ok) {
        throw new Error(
          `Backend error: ${result.status} - ${rawResponse}`
        );
      }

      // -----------------------------------------------------
      // PARSE JSON
      // -----------------------------------------------------
      let data;

      try {
        data = JSON.parse(rawResponse);
      } catch (parseError) {
        console.error("JSON PARSE ERROR:", parseError);

        throw new Error(
          "Backend returned an invalid JSON response."
        );
      }

      console.log("PARSED RESPONSE:");
      console.log(data);

      // -----------------------------------------------------
      // EXTRACT AI RESPONSE
      // -----------------------------------------------------
      const aiResponse = extractAIResponse(data);

      console.log("AI RESPONSE:", aiResponse);

      // -----------------------------------------------------
      // ADD ASSISTANT MESSAGE
      // -----------------------------------------------------
      setMessages((previousMessages) => [
        ...previousMessages,
        {
          role: "assistant",
          text: aiResponse,
        },
      ]);

      // Optional voice response
      // speak(aiResponse);

    } catch (error) {
      console.error("=================================");
      console.error("CHAT ERROR:");
      console.error(error);
      console.error("=================================");

      setMessages((previousMessages) => [
        ...previousMessages,
        {
          role: "assistant",
          text:
            "Sorry, I couldn't connect to the HolidayBreakz support system. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  // =========================================================
  // TEXT TO SPEECH
  // =========================================================
  function speak(text) {
    if (!text) {
      return;
    }

    if (!window.speechSynthesis) {
      return;
    }

    const speech = new SpeechSynthesisUtterance(text);

    speech.lang = "en-IN";
    speech.rate = 1;
    speech.pitch = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(speech);
  }

  // =========================================================
  // VOICE INPUT
  // =========================================================
  function startListening() {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert(
        "Speech recognition is not available in this browser. Please use Google Chrome."
      );

      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.continuous = false;

    setListening(true);

    recognition.onstart = () => {
      console.log("Voice recognition started");
    };

    recognition.onresult = async (event) => {
      const text =
        event.results[0][0].transcript;

      console.log("VOICE MESSAGE:", text);

      setListening(false);

      await sendMessage(text);
    };

    recognition.onerror = (event) => {
      console.error(
        "SPEECH ERROR:",
        event.error
      );

      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };

    try {
      recognition.start();
    } catch (error) {
      console.error(
        "Could not start speech recognition:",
        error
      );

      setListening(false);
    }
  }

  // =========================================================
  // QUICK ACTION
  // =========================================================
  function quickMessage(text) {
    sendMessage(text);
  }

  // =========================================================
  // UI
  // =========================================================
  return (
    <>
      {/* =====================================================
          LANDING PAGE
          ===================================================== */}
      <LandingPage />

      {/* =====================================================
          EXISTING CHATBOT
          ===================================================== */}
      <div className="travel-agent-container">

        {/* ===================================================
            SMALL AGENT
            =================================================== */}
        {agentState === "small" && (
          <button
            className="agent-small-button"
            onClick={handleAgentClick}
            aria-label="Open HolidayBreakz AI Agent"
          >
            <img
              src="https://static.naukimg.com/s/0/0/i/job-agent/pwa/v0/agent_icon.gif"
              alt="HolidayBreakz AI Travel Agent"
            />
          </button>
        )}

        {/* ===================================================
            LARGE AGENT
            =================================================== */}
        {agentState === "large" && (
          <div className="agent-overlay">

            <div className="large-agent-wrapper">

              <button
                className="large-agent-button"
                onClick={handleAgentClick}
                aria-label="Start HolidayBreakz AI Assistant"
              >
                <img
                  src="https://static.naukimg.com/s/0/0/i/job-agent/pwa/v0/agent_icon.gif"
                  alt="HolidayBreakz AI"
                />
              </button>

              <div className="agent-welcome-text">

                <h2>
                  Hi! 👋
                </h2>

                <p>
                  I'm your HolidayBreakz
                  <br />
                  AI Travel Assistant
                </p>

                <span>
                  Click me to start chatting
                </span>

              </div>

              <button
                className="large-agent-close"
                onClick={closeAgent}
                aria-label="Close"
              >
                ✕
              </button>

            </div>

          </div>
        )}

        {/* ===================================================
            CHAT
            =================================================== */}
        {agentState === "chat" && (
          <div className="chat-overlay">

            <div className="travel-chat-window">

              {/* =================================================
                  HEADER
                  ================================================= */}
              <div className="travel-chat-header">

                <div className="header-agent">

                  <img
                    src="https://static.naukimg.com/s/0/0/i/job-agent/pwa/v0/agent_icon.gif"
                    alt="HolidayBreakz AI"
                  />

                  <div>

                    <strong>
                      HolidayBreakz AI
                    </strong>

                    <small>
                      ● Online
                    </small>

                  </div>

                </div>

                <button
                  className="chat-close"
                  onClick={closeAgent}
                  aria-label="Close chat"
                >
                  ✕
                </button>

              </div>

              {/* =================================================
                  CHAT BODY
                  ================================================= */}
              <div
                className="travel-chat-body"
                ref={chatBodyRef}
              >

                {/* =================================================
                    QUICK ACTIONS
                    ================================================= */}
                {messages.length === 1 && (
                  <div className="quick-actions">

                    <p>
                      How can I help you?
                    </p>

                    <button
                      onClick={() =>
                        quickMessage(
                          "What holiday packages does HolidayBreakz provide?"
                        )
                      }
                    >
                      🏖️ Holiday Packages
                    </button>

                    <button
                      onClick={() =>
                        quickMessage(
                          "What information do I need to provide for booking?"
                        )
                      }
                    >
                      📋 Booking Information
                    </button>

                    <button
                      onClick={() =>
                        quickMessage(
                          "How can I cancel my booking?"
                        )
                      }
                    >
                      ❌ Cancel Booking
                    </button>

                    <button
                      onClick={() =>
                        quickMessage(
                          "What is the cancellation policy?"
                        )
                      }
                    >
                      📄 Cancellation Policy
                    </button>

                    <button
                      onClick={() =>
                        quickMessage(
                          "What information is available about refunds?"
                        )
                      }
                    >
                      💰 Refund Information
                    </button>

                  </div>
                )}

                {/* =================================================
                    MESSAGES
                    ================================================= */}
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={
                      msg.role === "user"
                        ? "chat-message user-message"
                        : "chat-message assistant-message"
                    }
                  >

                    {/* ASSISTANT AVATAR */}
                    {msg.role === "assistant" && (
                      <div className="message-avatar">
                        🤖
                      </div>
                    )}

                    {/* MESSAGE */}
                    <div className="message-bubble">
                      {msg.text}

                      {/* Typing cursor */}
                      {loading &&
                        index === messages.length - 1 &&
                        msg.role === "assistant" && (
                          <span className="typing-cursor">
                            ▌
                          </span>
                        )}
                    </div>

                  </div>
                ))}

                {/* =================================================
                    THINKING INDICATOR
                    ================================================= */}
                {loading &&
                  messages[messages.length - 1]?.role ===
                    "user" && (

                  <div className="chat-message assistant-message">

                    <div className="message-avatar">
                      🤖
                    </div>

                    <div className="message-bubble thinking">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>

                  </div>
                )}

              </div>

              {/* =================================================
                  INPUT AREA
                  ================================================= */}
              <div className="travel-chat-input">

                <input
                  type="text"
                  placeholder="Ask about your trip..."
                  value={message}
                  disabled={loading}
                  onChange={(e) =>
                    setMessage(e.target.value)
                  }
                  onKeyDown={(e) => {
                    if (
                      e.key === "Enter" &&
                      !loading
                    ) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                />

                {/* =================================================
                    VOICE BUTTON
                    ================================================= */}
                <button
                  className={
                    listening
                      ? "voice-button listening"
                      : "voice-button"
                  }
                  onClick={startListening}
                  disabled={listening || loading}
                  title="Voice input"
                  aria-label="Voice input"
                >
                  {listening ? "🔴" : "🎤"}
                </button>

                {/* =================================================
                    SEND BUTTON
                    ================================================= */}
                <button
                  className="send-button"
                  onClick={() => sendMessage()}
                  disabled={
                    loading ||
                    !message.trim()
                  }
                  title="Send message"
                  aria-label="Send message"
                >
                  ➤
                </button>

              </div>

            </div>

          </div>
        )}

      </div>
    </>
  );
}
