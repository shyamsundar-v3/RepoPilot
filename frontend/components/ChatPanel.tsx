"use client";

import { useState } from "react";
import { chatWithRepo } from "@/lib/api";
import { ChatResponse } from "@/lib/types";
import ChatMessage from "./ChatMessage";

interface Message {
  role: "user" | "assistant";
  text: string;
  response?: ChatResponse;
}

interface Props {
  repoId: string;
}

export default function ChatPanel({ repoId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    const question = input.trim();
    if (!question) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    try {
      const res = await chatWithRepo({ repo_id: repoId, question });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: res.answer, response: res },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${e.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="border border-gray-700 rounded-lg overflow-hidden">
      <div className="bg-gray-900 px-4 py-2 border-b border-gray-700">
        <h3 className="text-sm font-medium text-gray-300">Chat with this repo</h3>
      </div>
      <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-gray-500 text-sm">Ask a question about this repository...</p>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} text={msg.text} response={msg.response} />
        ))}
        {loading && <p className="text-gray-500 text-sm">Thinking...</p>}
      </div>
      <div className="border-t border-gray-700 p-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !loading && handleSend()}
          placeholder="Ask a question..."
          className="flex-1 px-3 py-2 rounded bg-gray-800 border border-gray-700 text-gray-100 text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="px-4 py-2 rounded bg-blue-600 text-white text-sm hover:bg-blue-500 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
