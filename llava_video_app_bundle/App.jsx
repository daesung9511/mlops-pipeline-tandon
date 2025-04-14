import React, { useState } from 'react';
import axios from 'axios';
import * as XLSX from 'xlsx';

export default function App() {
  const [videos, setVideos] = useState([{ file: null, questions: [''] }]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVideoChange = (index, file) => {
    const updated = [...videos];
    updated[index].file = file;
    // questions가 없거나 배열이 아닌 경우 초기화
    if (!updated[index].questions || !Array.isArray(updated[index].questions)) {
      updated[index].questions = [''];
    }
    setVideos(updated);
  };

  const handleQuestionChange = (vIndex, qIndex, value) => {
    const updated = [...videos];
    if (!updated[vIndex].questions || !Array.isArray(updated[vIndex].questions)) {
      updated[vIndex].questions = [''];
    }
    updated[vIndex].questions[qIndex] = value;
    setVideos(updated);
  };

  const addVideo = () => {
    if (videos.length >= 10) return;
    setVideos([...videos, { file: null, questions: [''] }]);
  };

  const addQuestion = (vIndex) => {
    const updated = [...videos];
    // questions 배열이 없거나 배열이 아니라면 초기화
    if (!updated[vIndex].questions || !Array.isArray(updated[vIndex].questions)) {
      updated[vIndex].questions = [''];
    }
    if (updated[vIndex].questions.length >= 10) return;
    updated[vIndex].questions.push('');
    setVideos(updated);
  };

  const handleDownloadExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(results);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Results');
    XLSX.writeFile(workbook, 'llava_results.xlsx');
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    let allQuestions = [];

    for (let v of videos) {
      if (v.file) formData.append('files', v.file);
      if (v.questions && Array.isArray(v.questions)) {
        allQuestions.push(...v.questions);
      }
    }

    if (allQuestions.length === 0) {
      setError('Please enter at least one question.');
      return;
    }

    allQuestions.forEach((q) => formData.append('questions', q));

    try {
      setError('');
      setLoading(true);
      const res = await axios.post('http://129.114.109.0:8000/ask_video/', formData);
      // 결과가 undefined인 경우 빈 배열을 사용
      setResults(res.data.results || []);
    } catch (err) {
      console.error(err);
      setError('Something went wrong while submitting.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-2xl font-bold">LLaVA Video Questioner</h1>

      {error && <div className="text-red-600 font-medium">{error}</div>}

      {videos.map((video, vIndex) => (
        <div key={vIndex} className="border p-4 rounded space-y-2">
          <label className="font-medium">Video {vIndex + 1}</label>
          <input
            type="file"
            accept="video/mp4"
            onChange={(e) => handleVideoChange(vIndex, e.target.files[0])}
          />

          {Array.isArray(video.questions) && video.questions.map((q, qIndex) => (
            <input
              key={qIndex}
              type="text"
              placeholder={`Question ${qIndex + 1}`}
              value={q}
              onChange={(e) => handleQuestionChange(vIndex, qIndex, e.target.value)}
              className="border p-2 w-full"
            />
          ))}

          {Array.isArray(video.questions) && video.questions.length < 10 && (
            <button onClick={() => addQuestion(vIndex)} className="text-blue-600">
              ➕ Add Question
            </button>
          )}
        </div>
      ))}

      {videos.length < 10 && (
        <button onClick={addVideo} className="bg-gray-200 px-3 py-1 rounded">
          ➕ Add Another Video
        </button>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="bg-blue-600 text-white px-4 py-2 rounded shadow"
      >
        {loading ? 'Processing...' : 'Submit'}
      </button>

      {loading && <p className="text-gray-600">⏳ Please wait, analyzing videos...</p>}

      {Array.isArray(results) && results.length > 0 && (
        <div className="mt-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold mb-2">Results:</h2>
            <button onClick={handleDownloadExcel} className="bg-green-600 text-white px-3 py-1 rounded">
              📥 Download Excel
            </button>
          </div>

          <ul className="space-y-2">
            {results.map((r, i) => (
              <li key={i} className="border p-2 rounded">
                <strong>File:</strong> {r.filename}<br />
                <strong>Q:</strong> {r.question}<br />
                <strong>A:</strong> {r.answer}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
