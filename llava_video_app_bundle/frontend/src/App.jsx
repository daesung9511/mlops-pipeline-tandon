import React, { useState } from 'react';
import axios from 'axios';

export default function App() {
  const [videos, setVideos] = useState([{ file: null, questions: [''] }]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  const handleVideoChange = (index, file) => {
    const updated = [...videos];
    updated[index].file = file;
    setVideos(updated);
  };

  const handleQuestionChange = (vIndex, qIndex, value) => {
    const updated = [...videos];
    updated[vIndex].questions[qIndex] = value;
    setVideos(updated);
  };

  const addVideo = () => {
    if (videos.length >= 10) return;
    setVideos([...videos, { file: null, questions: [''] }]);
  };

  const addQuestion = (vIndex) => {
    const updated = [...videos];
    if (updated[vIndex].questions.length < 10) {
      updated[vIndex].questions.push('');
      setVideos(updated);
    }
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    let hasQuestion = false;

    videos.forEach((video) => {
      if (video.file) {
        formData.append('files', video.file);
      }
      video.questions.forEach((q) => {
        if (q.trim()) {
          formData.append('questions', q);
          hasQuestion = true;
        }
      });
    });

    if (!hasQuestion) {
      setError('At least one question is required.');
      return;
    }

    try {
      setLoading(true);
      setError('');
      const response = await axios.post('http://129.114.109.15:8000/ask_video/', formData);
      setResults(response.data.results || []);
    } catch (err) {
      setError('Failed to submit. Please check server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">LLaVA Video QA</h1>

      {videos.map((video, vIdx) => (
        <div key={vIdx} className="border p-4 rounded-md space-y-3">
          <div>
            <label>🎬 Video {vIdx + 1}</label><br />
            <input
              type="file"
              accept="video/*"
              onChange={(e) => handleVideoChange(vIdx, e.target.files[0])}
            />
          </div>

          {video.questions.map((q, qIdx) => (
            <input
              key={qIdx}
              type="text"
              placeholder={`Question ${qIdx + 1}`}
              value={q}
              onChange={(e) => handleQuestionChange(vIdx, qIdx, e.target.value)}
              className="w-full border px-2 py-1 rounded mt-1"
            />
          ))}

          {video.questions.length < 10 && (
            <button
              onClick={() => addQuestion(vIdx)}
              className="text-blue-600 underline text-sm"
            >
              ➕ Add Question
            </button>
          )}
        </div>
      ))}

      {videos.length < 10 && (
        <button
          onClick={addVideo}
          className="bg-gray-200 px-4 py-2 rounded shadow text-sm"
        >
          ➕ Add Another Video
        </button>
      )}

      {error && <div className="text-red-600 font-medium">{error}</div>}

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="bg-blue-600 text-white px-6 py-2 rounded"
      >
        {loading ? 'Submitting...' : 'Submit'}
      </button>

      {results.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-bold mb-2">Results</h2>
          <ul className="space-y-2">
            {results.map((res, i) => (
              <li key={i} className="border p-2 rounded">
                <strong>📁 File:</strong> {res.filename}<br />
                <strong>❓ Question:</strong> {res.question}<br />
                <strong>💬 Answer:</strong> {res.answer || res.error}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
