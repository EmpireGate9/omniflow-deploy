import { useState, useEffect } from "react";
import { API_BASE_URL } from "./config";

export default function App() {
  const [domains, setDomains] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);

  // تحميل المجالات
  useEffect(() => {
    fetch(`${API_BASE_URL}/domains`)
      .then(res => res.json())
      .then(data => setDomains(data))
      .catch(() => setDomains([]));
  }, []);

  // تحميل السجلات
  const loadArtifacts = () => {
    fetch(`${API_BASE_URL}/artifacts`)
      .then(res => res.json())
      .then(data => setArtifacts(data))
      .catch(() => setArtifacts([]));
  };

  useEffect(() => {
    loadArtifacts();
  }, []);

  // إرسال رسالة
  const sendMessage = async () => {
    if (!message.trim()) return;

    setLoading(true);
    setReply("");

    try {
      const res = await fetch(`${API_BASE_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ payload: message })
      });

      const data = await res.json();
      setReply(data.result || JSON.stringify(data));
      setMessage("");
      loadArtifacts();
    } catch (err) {
      setReply("❌ خطأ في الاتصال بالخادم");
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h2>OmniFlow Assistant ✅</h2>

      <h3>المجالات المتاحة:</h3>
      {domains.length === 0 ? <p>جاري التحميل...</p> : (
        <ul>
          {domains.map((d, i) => (
            <li key={i}>{d.name} — {d.description}</li>
          ))}
        </ul>
      )}

      <h3>أرسل سؤال</h3>
      <textarea
        rows="3"
        style={{ width: "100%", padding: "10px" }}
        value={message}
        onChange={e => setMessage(e.target.value)}
      ></textarea>
      <button onClick={sendMessage} disabled={loading}>
        {loading ? "يرسل..." : "إرسال"}
      </button>

      <h3>الرد:</h3>
      <div style={{ background: "#eee", padding: "10px", minHeight: "80px" }}>
        {reply}
      </div>

      <h3>السجلات:</h3>
      <div style={{ maxHeight: "200px", overflow: "auto", border: "1px solid #ccc", padding: "10px" }}>
        {artifacts.length === 0 ? (
          <p>لا توجد سجلات بعد</p>
        ) : (
          artifacts.map((a, i) => (
            <div key={i} style={{ marginBottom: "10px" }}>
              <strong>{a.domain}</strong> — {a.kind}<br />
              <small>{a.created_at}</small>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
