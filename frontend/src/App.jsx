import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  Phone, 
  Languages, 
  Search, 
  Trash2, 
  Eye, 
  RefreshCw, 
  CheckCircle2, 
  Globe,
  X
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api/phone';

// Main Phone Parser Dashboard Component integrated with Axios
export default function App() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [languageFilter, setLanguageFilter] = useState('All');
  const [selectedTranscript, setSelectedTranscript] = useState(null);

  // Fetch phone records from FastAPI backend endpoint via Axios GET
  const fetchRecords = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(API_BASE_URL);
      setRecords(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error fetching records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  // Delete a phone record by database ID via Axios DELETE
  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this phone record?')) return;
    try {
      await axios.delete(`${API_BASE_URL}/${id}`);
      setRecords((prev) => prev.filter((rec) => rec.id !== id));
    } catch (err) {
      alert(err.response?.data?.detail || err.message || 'Delete operation failed');
    }
  };

  // Calculate metrics breakdown by language presence
  const metrics = useMemo(() => {
    const total = records.length;
    const enCount = records.filter((r) => r.language === 'en').length;
    const hiCount = records.filter((r) => r.language === 'hi').length;
    const mixedCount = records.filter((r) => r.language === 'mixed').length;
    return { total, enCount, hiCount, mixedCount };
  }, [records]);

  // Filter records based on search term and language dropdown selection
  const filteredRecords = useMemo(() => {
    return records.filter((record) => {
      const matchesSearch =
        record.parsedNumber.includes(searchQuery) ||
        record.rawTranscript.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesLang =
        languageFilter === 'All' ||
        record.language.toLowerCase() === languageFilter.toLowerCase();

      return matchesSearch && matchesLang;
    });
  }, [records, searchQuery, languageFilter]);

  // Render language tag badge with proper styling
  const renderLanguageBadge = (lang) => {
    switch (lang ? lang.toLowerCase() : '') {
      case 'en':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-900/50 text-blue-300 border border-blue-700/50">English (en)</span>;
      case 'hi':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-orange-900/50 text-orange-300 border border-orange-700/50">Hindi (hi)</span>;
      case 'mixed':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-purple-900/50 text-purple-300 border border-purple-700/50">Hinglish (mixed)</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-800 text-gray-300">{lang}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header Title */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Phone className="w-8 h-8 text-indigo-400" />
              Voice Phone Number Collector
            </h1>
            <p className="text-gray-400 mt-1">Real-time parsing & database collection dashboard</p>
          </div>
          <button
            onClick={fetchRecords}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm font-medium transition duration-200 self-start md:self-auto cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            Refresh Data
          </button>
        </div>

        {/* Metrics Header Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
            <div className="flex justify-between items-center text-gray-400">
              <span className="text-sm font-medium">Total Numbers</span>
              <Phone className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="text-3xl font-extrabold text-white mt-2">{metrics.total}</div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
            <div className="flex justify-between items-center text-gray-400">
              <span className="text-sm font-medium">English (en)</span>
              <Globe className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-3xl font-extrabold text-blue-400 mt-2">{metrics.enCount}</div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
            <div className="flex justify-between items-center text-gray-400">
              <span className="text-sm font-medium">Hindi (hi)</span>
              <Languages className="w-5 h-5 text-orange-400" />
            </div>
            <div className="text-3xl font-extrabold text-orange-400 mt-2">{metrics.hiCount}</div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
            <div className="flex justify-between items-center text-gray-400">
              <span className="text-sm font-medium">Hinglish (mixed)</span>
              <CheckCircle2 className="w-5 h-5 text-purple-400" />
            </div>
            <div className="text-3xl font-extrabold text-purple-400 mt-2">{metrics.mixedCount}</div>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row gap-4 bg-gray-900 p-4 rounded-xl border border-gray-800">
          <div className="relative flex-grow">
            <Search className="w-5 h-5 absolute left-3.5 top-3 text-gray-500" />
            <input
              type="text"
              placeholder="Search by phone number or raw transcript..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-950 border border-gray-800 rounded-lg text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400 whitespace-nowrap">Language:</span>
            <select
              value={languageFilter}
              onChange={(e) => setLanguageFilter(e.target.value)}
              className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500 transition cursor-pointer"
            >
              <option value="All">All Languages</option>
              <option value="en">English (en)</option>
              <option value="hi">Hindi (hi)</option>
              <option value="mixed">Hinglish (mixed)</option>
            </select>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="bg-red-950/80 border border-red-800 text-red-300 px-4 py-3 rounded-xl text-sm">
            {error}
          </div>
        )}

        {/* Records Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-gray-950 text-gray-400 uppercase text-xs border-b border-gray-800">
                <tr>
                  <th className="px-6 py-4 font-semibold">Parsed Number</th>
                  <th className="px-6 py-4 font-semibold">Language</th>
                  <th className="px-6 py-4 font-semibold">Collected At</th>
                  <th className="px-6 py-4 font-semibold">Raw Transcript</th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
                      Loading phone records...
                    </td>
                  </tr>
                ) : filteredRecords.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                      No matching records found.
                    </td>
                  </tr>
                ) : (
                  filteredRecords.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-800/40 transition">
                      <td className="px-6 py-4 font-mono font-medium text-white text-base">
                        {record.parsedNumber}
                      </td>
                      <td className="px-6 py-4">
                        {renderLanguageBadge(record.language)}
                      </td>
                      <td className="px-6 py-4 text-gray-400 whitespace-nowrap">
                        {new Date(record.collectedAt).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 max-w-xs truncate text-gray-400">
                        {record.rawTranscript}
                      </td>
                      <td className="px-6 py-4 text-right space-x-2 whitespace-nowrap">
                        <button
                          onClick={() => setSelectedTranscript(record)}
                          className="p-1.5 bg-gray-800 hover:bg-gray-700 text-indigo-400 rounded-md transition cursor-pointer"
                          title="View Raw Transcript"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(record.id)}
                          className="p-1.5 bg-gray-800 hover:bg-red-900/50 text-red-400 rounded-md transition cursor-pointer"
                          title="Delete Record"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Raw Transcript Modal */}
        {selectedTranscript && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
            <div className="bg-gray-900 border border-gray-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
              <div className="flex justify-between items-center border-b border-gray-800 pb-3">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Phone className="w-5 h-5 text-indigo-400" />
                  Record Details #{selectedTranscript.id}
                </h3>
                <button
                  onClick={() => setSelectedTranscript(null)}
                  className="text-gray-400 hover:text-white cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div>
                <span className="text-xs text-gray-400 uppercase font-semibold">Parsed Phone Number:</span>
                <p className="text-xl font-mono text-indigo-300 font-bold mt-1">{selectedTranscript.parsedNumber}</p>
              </div>
              <div>
                <span className="text-xs text-gray-400 uppercase font-semibold">Detected Language:</span>
                <div className="mt-1">{renderLanguageBadge(selectedTranscript.language)}</div>
              </div>
              <div>
                <span className="text-xs text-gray-400 uppercase font-semibold">Raw Transcript:</span>
                <div className="bg-gray-950 p-3 rounded-lg border border-gray-800 text-sm font-mono text-gray-200 mt-1 whitespace-pre-wrap">
                  {selectedTranscript.rawTranscript}
                </div>
              </div>
              <div className="pt-2 text-right">
                <button
                  onClick={() => setSelectedTranscript(null)}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
