import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, Moon, Sun, Database } from 'lucide-react';
import axios from 'axios';
import FileUpload from './components/FileUpload';
import DataPreview from './components/DataPreview';
import ChatInterface from './components/ChatInterface';
import LoadingSpinner from './components/LoadingSpinner';
import ResultCards from './components/ResultCards';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [profile, setProfile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [error, setError] = useState(null);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [viewMode, setViewMode] = useState('dashboard'); // 'dashboard' or 'viz'

  // ── Theme ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  // ── URL-based Session Restore on page refresh ─────────────────────────────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sid = params.get('session');
    if (sid) {
      restoreSession(sid);
    }
  }, []);

  const restoreSession = async (sid) => {
    setIsLoading(true);
    setLoadingMessage('Restoring your previous session...');
    try {
      const res = await axios.get(`${API_URL}/api/session/${sid}`);
      setSessionId(res.data.session_id);
      setProfile(res.data.profile);
      setPreviewData(res.data.preview);
      setResults([]);
    } catch {
      // Session expired - just show upload screen, but clean URL
      window.history.replaceState({}, '', window.location.pathname);
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // ── Auto-clear error ──────────────────────────────────────────────────────
  useEffect(() => {
    if (error) {
      const t = setTimeout(() => setError(null), 5500);
      return () => clearTimeout(t);
    }
  }, [error]);

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleUploadSuccess = (data) => {
    setSessionId(data.session_id);
    setProfile(data.profile);
    setPreviewData(data.preview);

    // Automatically populate results with the 3 starter dashboard analyses
    if (data.automated_analysis) {
      setResults(data.automated_analysis.map((res, i) => ({
        ...res,
        id: `starter-${i}`,
        is_automated: true
      })));
      setIsChatOpen(true); // Open assistant to show the dashboard
    } else {
      setResults([]);
    }

    setError(null);
    window.history.replaceState({}, '', `?session=${data.session_id}`);
  };

  const handleError = (msg) => {
    setError(msg);
    setIsLoading(false);
  };

  const handleNewResult = (result) => {
    setResults(prev => [...prev, { ...result, id: Date.now() }]);
  };

  // Called by ChatInterface when Supabase history messages are loaded
  const handleHistoryLoaded = (messages) => {
    // Convert raw DB messages (role/content pairs) → display results
    // We group user+assistant pairs into pseudo-results for the chat UI
    const paired = [];
    for (let i = 0; i < messages.length; i++) {
      if (messages[i].role === 'user') {
        const assistant = messages[i + 1]?.role === 'assistant' ? messages[i + 1] : null;
        paired.push({
          id: `history-${i}`,
          question: messages[i].content,
          insight: assistant?.content || '',
          chart_json: null,
          generated_code: null,
          raw_result: null,
          from_history: true,
        });
        if (assistant) i++; // skip assistant message
      }
    }
    if (paired.length > 0) {
      setResults(paired);
    }
  };

  // ── Helper to safely get results that have VALID charts ──────────────────
  const getChartResults = () => {
    return results.filter(r => {
      // Always show starter dashboard items in the Viz tab, even if they failed to generate a chart
      if (r.is_automated) return true;

      // For user queries, only show them in the Viz tab if they actually produced a chart
      if (!r.chart_json) return false;
      try {
        const parsed = typeof r.chart_json === 'string' ? JSON.parse(r.chart_json) : r.chart_json;
        return parsed && Array.isArray(parsed.data) && parsed.data.length > 0;
      } catch {
        return false;
      }
    });
  };

  const chartResults = getChartResults();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-deep-950 text-slate-900 dark:text-slate-100 transition-colors duration-500 overflow-x-hidden">

      {/* ── Navbar ─────────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 w-full glass-panel dark:glass-dark border-b border-slate-200 dark:border-deep-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-3">
                <div className="bg-brand-500 p-2 rounded-xl text-white shadow-lg shadow-brand-500/30">
                  <BarChart3 className="w-6 h-6" />
                </div>
                <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-brand-500 to-fuchsia-500 dark:from-brand-400 dark:to-fuchsia-400">
                  AI Data Analyst
                </span>
              </div>

              {sessionId && (
                <div className="hidden md:flex items-center space-x-1">
                  <button
                    onClick={() => setViewMode('dashboard')}
                    className={`px-4 py-2 text-sm font-bold rounded-xl transition-all ${viewMode === 'dashboard' ? 'text-brand-500 bg-brand-500/10' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-deep-800'}`}
                  >
                    Dashboard
                  </button>
                  <button
                    onClick={() => setViewMode('viz')}
                    className={`px-4 py-2 text-sm font-bold rounded-xl transition-all ${viewMode === 'viz' ? 'text-brand-500 bg-brand-500/10' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-deep-800'}`}
                  >
                    Visualization
                  </button>
                </div>
              )}
            </div>

            <div className="flex items-center gap-3">
              {sessionId && (
                <button
                  onClick={() => setIsChatOpen(!isChatOpen)}
                  className={`flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded-xl transition-all border ${isChatOpen
                    ? 'bg-brand-500 text-white border-brand-400 shadow-lg shadow-brand-500/30'
                    : 'bg-white dark:bg-deep-800 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-deep-700'
                    }`}
                >
                  <Database className="w-4 h-4" />
                  {isChatOpen ? 'Close Assistant' : 'AI Assistant'}
                </button>
              )}
              <button
                onClick={() => setTheme(p => p === 'dark' ? 'light' : 'dark')}
                className="p-2 rounded-xl bg-slate-100 dark:bg-deep-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-deep-700 transition-all border border-slate-200 dark:border-deep-800"
              >
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex relative h-[calc(100vh-64px)] overflow-hidden">
        {/* ── Main Content Area ─────────────────────────────────────────────── */}
        <motion.main
          initial={false}
          animate={{
            width: isChatOpen ? 'calc(100% - 460px)' : '100%',
            opacity: 1
          }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="flex-1 px-4 sm:px-6 lg:px-8 py-8 space-y-8 min-w-0 overflow-y-auto"
        >

          {/* ── Error Banner ──────────────────────────────────────────────────── */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-red-50 text-red-600 border border-red-200 p-4 rounded-xl flex items-center shadow-lg"
              >
                <Database className="w-5 h-5 mr-3 flex-shrink-0" />
                <p>{error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Loading Overlay ───────────────────────────────────────────────── */}
          <AnimatePresence>
            {isLoading && (!sessionId || loadingMessage === 'Restoring your previous session...') && (
              <LoadingSpinner message={loadingMessage} />
            )}
          </AnimatePresence>

          {!sessionId ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              className="max-w-4xl mx-auto"
            >
              <FileUpload
                onSuccess={handleUploadSuccess}
                onError={handleError}
                setIsLoading={setIsLoading}
                setLoadingMessage={setLoadingMessage}
              />
            </motion.div>
          ) : (
            <div className="max-w-7xl mx-auto">
              <AnimatePresence mode="wait">
                {viewMode === 'dashboard' ? (
                  <motion.div
                    key="dashboard"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="space-y-8"
                  >
                    <DataPreview profile={profile} previewData={previewData} />
                  </motion.div>
                ) : (
                  <motion.div
                    key="viz"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="space-y-6"
                  >
                    <div className="flex flex-col space-y-2 mb-8 text-center">
                      <h2 className="text-3xl font-extrabold tracking-tight">Visualization Board</h2>
                      <p className="text-slate-500 dark:text-slate-400">All charts generated during this session.</p>
                    </div>

                     {chartResults.length > 0 ? (
                      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 pb-20">
                        {chartResults.map((res) => (
                          <ResultCards key={res.id} result={res} isVisualizationBoard={true} />
                        ))}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-20 text-center opacity-50">
                        <BarChart3 className="w-16 h-16 mb-4" />
                        <p className="text-lg font-medium">No charts have been generated yet.</p>
                        <p className="text-sm">Ask the assistant to visualize data to see icons here.</p>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </motion.main>

        {/* ── Side-Panel Chat Interface ────────────────────────────────────── */}
        <ChatInterface
          sessionId={sessionId}
          profile={profile}
          results={results}
          onResult={handleNewResult}
          onError={handleError}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          loadingMessage={loadingMessage}
          setLoadingMessage={setLoadingMessage}
          onHistoryLoaded={handleHistoryLoaded}
          isOpen={isChatOpen}
          onToggle={() => setIsChatOpen(!isChatOpen)}
        />
      </div>
    </div>
  );
}

export default App;