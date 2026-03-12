import { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, Loader2, RefreshCw } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const QueryInterface = ({
    sessionId,
    profile,
    onResult,
    onError,
    setIsLoading,
    setLoadingMessage,
    isLoading,
    isCompact = false,
}) => {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [suggestionsLoading, setSuggestionsLoading] = useState(false);
    const inputRef = useRef(null);

    // ── AI-powered Smart Suggestions from Supabase ───────────────────────────
    useEffect(() => {
        if (!sessionId) return;
        setSuggestions([]);
        fetchSuggestions();
    }, [sessionId]);

    const fetchSuggestions = async () => {
        setSuggestionsLoading(true);
        try {
            const res = await axios.post(`${API_URL}/api/generate-suggestions`, {
                session_id: sessionId,
            });
            setSuggestions(res.data.suggestions || []);
        } catch {
            // Fall back to local heuristics if AI suggestions fail
            setSuggestions(buildLocalSuggestions(profile));
        } finally {
            setSuggestionsLoading(false);
        }
    };

    const buildLocalSuggestions = (p) => {
        if (!p?.columns) return [];
        const numCols = p.columns.filter(c => c.type === 'numeric');
        const textCols = p.columns.filter(c => c.type === 'text' || c.type === 'categorical');
        const dateCols = p.columns.filter(c => c.type === 'datetime');
        const ideas = [];
        if (numCols.length > 0 && textCols.length > 0) {
            ideas.push(`Show total ${numCols[0].name} by ${textCols[0].name}`);
            ideas.push(`Which ${textCols[0].name} has the highest ${numCols[0].name}?`);
        }
        if (dateCols.length > 0 && numCols.length > 0) {
            ideas.push(`Show the trend of ${numCols[0].name} over time`);
        }
        if (numCols.length >= 2) {
            ideas.push(`Is there a relationship between ${numCols[0].name} and ${numCols[1].name}?`);
        }
        if (ideas.length === 0 && numCols.length > 0) {
            ideas.push(`What is the average ${numCols[0].name}?`);
        }
        return ideas.slice(0, 4);
    };

    // ── Submit ────────────────────────────────────────────────────────────────
    const handleSubmit = async (e) => {
        e?.preventDefault();
        const q = query.trim();
        if (!q || isLoading) return;

        setIsLoading(true);
        setLoadingMessage('Initializing analysis...');
        setQuery('');

        try {
            const response = await fetch(`${API_URL}/api/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, question: q }),
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let finalData = null;

            let buffer = '';
            while (true) {
                const { value, done } = await reader.read();
                
                if (value) {
                    buffer += decoder.decode(value, { stream: !done });
                    const parts = buffer.split('\n\n');
                    
                    // Keep the last (potentially partial) part in the buffer
                    buffer = parts.pop() || '';

                    for (const part of parts) {
                        const trimmedPart = part.trim();
                        if (!trimmedPart || !trimmedPart.startsWith('data: ')) continue;
                        
                        try {
                            const data = JSON.parse(trimmedPart.replace(/^data: /, ''));
                            if (data.status) {
                                setLoadingMessage(data.status);
                            } else if (data.final_result) {
                                finalData = data.final_result;
                                break; // Got what we need, don't wait for stream to close
                            } else if (data.error) {
                                throw new Error(data.error);
                            }
                        } catch (e) {
                            console.error('Error parsing stream part:', e, trimmedPart);
                        }
                    }
                }
                
                if (done) {
                    // Process any remaining data in the buffer after stream ends
                    if (buffer && buffer.trim().startsWith('data: ')) {
                        try {
                            const data = JSON.parse(buffer.trim().replace('data: ', ''));
                            if (data.final_result) finalData = data.final_result;
                        } catch (e) {
                            console.error('Final buffer parse error:', e);
                        }
                    }
                    break;
                }
            }

            if (finalData) {
                onResult({ question: q, ...finalData });
            } else {
                onError("The analyst finished without a conclusion. This might be a connection issue or a backend skip.");
            }
            inputRef.current?.focus();
        } catch (err) {
            onError(err.message || 'Failed to analyze data. Please try again.');
        } finally {
            setIsLoading(false);
            setLoadingMessage('');
        }
    };

    const handleSuggestionClick = (s) => {
        setQuery(s);
        inputRef.current?.focus();
    };

    return (
        <div className={isCompact ? '' : 'glass-panel dark:glass-dark rounded-3xl p-6 shadow-md border border-slate-200 dark:border-deep-800 bg-white/40 dark:bg-deep-900/40 backdrop-blur-xl'}>
            <form onSubmit={handleSubmit} className="relative">
                <div className="relative flex items-center">
                    <Sparkles className={`absolute ${isCompact ? 'left-4' : 'left-6'} w-5 h-5 text-brand-400 pointer-events-none`} />
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        disabled={isLoading}
                        placeholder="Ask anything about your data..."
                        className={`w-full pr-14 bg-white/50 dark:bg-deep-950/50 rounded-2xl border-2 border-slate-200 dark:border-deep-800 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/20 outline-none transition-all text-slate-800 dark:text-slate-100 placeholder-slate-400 disabled:opacity-50 ${isCompact ? 'pl-12 py-3.5 text-base' : 'pl-16 py-5 text-lg'}`}
                    />
                    <button
                        type="submit"
                        disabled={!query.trim() || isLoading}
                        className={`absolute ${isCompact ? 'right-2' : 'right-4'} p-2.5 bg-brand-500 hover:bg-brand-600 disabled:bg-slate-300 dark:disabled:bg-deep-800 text-white rounded-xl transition-colors shadow-sm disabled:cursor-not-allowed`}
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </form>

            {/* Smart Suggestions */}
            {!isCompact && (
                <div className="mt-4 flex flex-wrap gap-2 items-center px-2 min-h-[2.5rem]">
                    {suggestionsLoading ? (
                        <span className="flex items-center gap-2 text-sm text-slate-400">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Generating AI suggestions...
                        </span>
                    ) : suggestions.length > 0 ? (
                        <>
                            <span className="text-sm font-medium text-slate-500 dark:text-slate-400 mr-1 flex items-center gap-1">
                                <Sparkles className="w-3.5 h-3.5 text-brand-400" /> AI Suggests:
                            </span>
                            {suggestions.map((s, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleSuggestionClick(s)}
                                    disabled={isLoading}
                                    className="px-4 py-2 rounded-full text-sm font-medium bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-300 hover:bg-brand-100 dark:hover:bg-brand-900/40 transition-colors border border-brand-200 dark:border-brand-500/30 hover:border-brand-400 disabled:opacity-50 whitespace-nowrap"
                                >
                                    {s}
                                </button>
                            ))}
                            <button
                                onClick={fetchSuggestions}
                                disabled={suggestionsLoading || isLoading}
                                title="Refresh suggestions"
                                className="p-1.5 text-slate-400 hover:text-brand-500 transition-colors"
                            >
                                <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                        </>
                    ) : null}
                </div>
            )}

            {/* Compact mode: show suggestions as small chips inside chat */}
            {isCompact && suggestions.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                    {suggestions.slice(0, 3).map((s, idx) => (
                        <button
                            key={idx}
                            onClick={() => handleSuggestionClick(s)}
                            disabled={isLoading}
                            className="px-3 py-1 rounded-full text-xs font-medium bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-300 hover:bg-brand-100 border border-brand-200 dark:border-brand-500/30 transition-colors disabled:opacity-50 whitespace-nowrap"
                        >
                            {s}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

export default QueryInterface;