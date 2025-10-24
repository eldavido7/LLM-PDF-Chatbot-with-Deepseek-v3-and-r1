import { FaInfoCircle, FaVolumeUp, FaArrowLeft, FaPaperPlane } from "react-icons/fa";
import React, { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "../store";
import { motion, AnimatePresence } from "framer-motion";
import { sendChatQuery } from "../app/api/chat.service";
import { addMessage, setLoading, setError } from "../app/api/chat.slice";
import Loader from "../Load";
import { toast } from "sonner";
import Image from "next/image";

interface ChatInterfaceProps {
  onBack: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onBack }) => {
  const [question, setQuestion] = useState("");
  const [enableSummarization, setEnableSummarization] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dispatch = useDispatch();

  const { sessionId, messages, isLoading } = useSelector(
    (state: RootState) => state.chat
  );

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [question]);

  const handleQuestionSubmit = async () => {
    if (!question.trim() || !sessionId) return;

    const tempQuestion = question.trim();
    setQuestion("");

    dispatch(addMessage({ type: "question", text: tempQuestion }));
    dispatch(setLoading(true));

    try {
      const result = await sendChatQuery(
        tempQuestion,
        sessionId,
        enableSummarization
      );

      if (result.success) {
        dispatch(addMessage({ type: "answer", text: result.message }));
      } else {
        dispatch(setError(result.message));
      }
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleQuestionSubmit();
    }
  };

  const speakText = (text: string) => {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      speechSynthesis.speak(utterance);
    } else {
      toast.error("Your browser does not support text-to-speech.");
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header with glassmorphism */}
      <header className="backdrop-blur-xl bg-white/10 border-b border-white/20 shadow-lg relative z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={onBack}
            className="group flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-white font-medium transition-all duration-200 hover:scale-105"
          >
            <FaArrowLeft className="group-hover:-translate-x-1 transition-transform" />
            <span className="hidden sm:inline">Back</span>
          </button>

          <h1 className="text-xl font-bold text-white hidden md:block bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            SmartPDF Chat
          </h1>

          <div className="flex items-center gap-3">
            {/* Summarization Toggle */}
            <div className="relative">
              <label className="flex items-center gap-2 cursor-pointer group">
                <span className="text-sm text-white/80 hidden sm:inline">Summarize</span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={enableSummarization}
                    onChange={() => setEnableSummarization(!enableSummarization)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-white/20 rounded-full peer peer-checked:bg-gradient-to-r peer-checked:from-blue-500 peer-checked:to-purple-500 transition-all duration-300"></div>
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-all duration-300 peer-checked:translate-x-5"></div>
                </div>
              </label>
            </div>

            {/* Info Icon with Tooltip */}
            <div className="relative">
              <button
                title="info"
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                onClick={() => toast.info("Slower, but more concise responses")}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-white transition-all duration-200"
              >
                <FaInfoCircle size={18} />
              </button>
              <AnimatePresence>
                {showTooltip && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 top-full mt-2 w-56 p-3 z-50 bg-gray-900 text-white text-sm rounded-lg shadow-xl border border-white/10"
                  >
                    Slower, but more concise and comprehensive responses.
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 relative z-0">
        <div className="max-w-7xl mx-auto">
          {messages.length === 0 ? (
            <motion.div
              className="flex flex-col items-center justify-center h-full"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <motion.div
                className="relative mb-8"
                animate={{
                  y: [0, -10, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 blur-3xl opacity-30 rounded-full"></div>
                <Image
                  width={200}
                  height={200}
                  src="/ai-chat-bot.png"
                  alt="AI Assistant"
                  className="relative w-40 h-40 drop-shadow-2xl"
                />
              </motion.div>
              <motion.h2
                className="text-2xl font-bold text-white mb-2"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                Ready to Help
              </motion.h2>
              <motion.p
                className="text-white/60 text-center max-w-md"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                Ask me anything about your document. I&apos;m here to provide clear and helpful answers.
              </motion.p>
            </motion.div>
          ) : (
            <div className="space-y-6 pb-4">
              <AnimatePresence mode="popLayout">
                {messages.map((message, index) => (
                  <motion.div
                    key={`message-${index}`}
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.3 }}
                    className={`flex ${message.type === "question" ? "justify-end" : "justify-start"
                      }`}
                  >
                    {message.type === "answer" && (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center mr-3 flex-shrink-0 shadow-lg">
                        <span className="text-white font-bold text-sm">AI</span>
                      </div>
                    )}

                    <div className="flex flex-col max-w-[75%] gap-2">
                      <div
                        className={`relative p-4 rounded-2xl shadow-lg ${message.type === "question"
                          ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-tr-sm"
                          : "bg-white/10 backdrop-blur-md text-white border border-white/20 rounded-tl-sm"
                          }`}
                      >
                        <p className="leading-relaxed whitespace-pre-wrap">{message.text}</p>
                      </div>

                      {message.type === "answer" && (
                        <button
                          onClick={() => speakText(message.text)}
                          className="self-start flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-white text-sm transition-all duration-200 hover:scale-105"
                        >
                          <FaVolumeUp size={14} />
                          <span>Listen</span>
                        </button>
                      )}
                    </div>

                    {message.type === "question" && (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center ml-3 flex-shrink-0 shadow-lg">
                        <span className="text-white font-bold text-sm">U</span>
                      </div>
                    )}
                  </motion.div>
                ))}

                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex justify-start"
                  >
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center mr-3 flex-shrink-0 shadow-lg">
                      <span className="text-white font-bold text-sm">AI</span>
                    </div>
                    <div className="p-4 rounded-2xl rounded-tl-sm bg-white/10 backdrop-blur-md border border-white/20">
                      <Loader />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Area with glassmorphism */}
      <div className="border-t border-white/20 backdrop-blur-xl bg-white/10">
        <div className="max-w-7xl mx-auto p-4">
          <div className="flex items-end gap-3 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-2 shadow-lg">
            <textarea
              ref={textareaRef}
              className="flex-1 bg-transparent text-white placeholder-white/50 resize-none outline-none px-3 py-2 max-h-32"
              rows={1}
              placeholder="Ask me anything about your document..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              title="submit"
              onClick={handleQuestionSubmit}
              disabled={!question.trim() || isLoading}
              className={`p-3 rounded-xl transition-all duration-200 flex-shrink-0 ${question.trim() && !isLoading
                ? "bg-gradient-to-r from-blue-500 to-purple-500 hover:shadow-lg hover:scale-105 text-white"
                : "bg-white/10 text-white/40 cursor-not-allowed"
                }`}
            >
              <FaPaperPlane size={18} />
            </button>
          </div>
          <p className="text-white/40 text-xs text-center mt-2">
            Press Enter to send, Shift + Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;