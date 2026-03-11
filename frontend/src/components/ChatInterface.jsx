import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, Bot, User, Search } from 'lucide-react';
import QueryInterface from './QueryInterface';
import ResultCards from './ResultCards';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ChatInterface = ({
    sessionId,
    profile,
    results,
    onResult,
    onError,
    isLoading,
    setIsLoading,
    setLoadingMessage,
    onHistoryLoaded,
    isOpen,
    onToggle
}) => {
    const [historyLoading, setHistoryLoading] = useState(false);
    const scrollRef = useRef(null);

    // Auto-scroll to bottom on new message / open / loading
    useEffect(() => {
        if (scrollRef.current) {
            const scroll = () => {
                scrollRef.current.scrollTo({
                    top: scrollRef.current.scrollHeight,
                    behavior: 'smooth'
                });
            };
            // Small delay to ensure content is rendered
            const timeout = setTimeout(scroll, 100);
            return () => clearTimeout(timeout);
        }
    }, [results, isOpen, isLoading]);

    // ── Restore chat history from Supabase on open (first time only) ─────────
    useEffect(() => {
        if (!isOpen || !sessionId || results.length > 0) return;
        loadHistory();
    }, [isOpen, sessionId]);

    const loadHistory = async () => {
        setHistoryLoading(true);
        try {
            const res = await axios.get(`${API_URL}/api/history/${sessionId}`);
            const messages = res.data.messages || [];
            if (messages.length > 0 && onHistoryLoaded) {
                onHistoryLoaded(messages);
            }
        } catch {
            // Non-fatal: if history can't be loaded, just start fresh
        } finally {
            setHistoryLoading(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ x: '100%' }}
                    animate={{ x: 0 }}
                    exit={{ x: '100%' }}
                    transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                    className="fixed sm:relative top-0 right-0 z-40 w-full sm:w-[460px] h-full flex flex-col bg-white dark:bg-deep-900 border-l border-slate-200 dark:border-deep-800 shadow-2xl"
                >
                    {/* ── Header ───────────────────────────────────────── */}
                    <div className="px-6 py-4 bg-slate-50/80 dark:bg-deep-950/80 backdrop-blur-md border-b border-slate-200 dark:border-deep-800 flex items-center justify-between flex-shrink-0">
                        <div className="flex items-center space-x-3">
                            <div className="bg-brand-500 p-2 rounded-xl text-white">
                                <Bot className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="font-bold text-slate-800 dark:text-slate-100">AI Assistant</h3>
                                <div className="flex items-center gap-1.5 mt-0.5">
                                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                                    <p className="text-[10px] text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider">Memory Active</p>
                                </div>
                            </div>
                        </div>
                        <button 
                            onClick={onToggle} 
                            className="p-2 hover:bg-slate-200 dark:hover:bg-deep-800 rounded-xl transition-colors text-slate-400"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* ── Messages Area ─────────────────────────────────── */}
                    <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth">
                        {historyLoading && (
                            <div className="flex justify-center py-6">
                                <span className="text-sm text-slate-400 animate-pulse">Restoring conversation history...</span>
                            </div>
                        )}

                        {results.length === 0 && !historyLoading ? (
                            <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-6">
                                <div className="p-4 bg-brand-500/10 rounded-3xl">
                                    <Bot className="w-12 h-12 text-brand-500" />
                                </div>
                                <div>
                                    <h4 className="font-bold text-slate-800 dark:text-slate-100 mb-2">How can I help you today?</h4>
                                    <p className="text-sm text-slate-500 dark:text-slate-400">
                                        Ask me to analyze trends, find relationship, or generate summaries of your data.
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {results.map((res) => (
                                    <div key={res.id} className="space-y-4">
                                        {/* User Message */}
                                        <div className="flex justify-end">
                                            <div className="max-w-[85%] bg-brand-500 text-white rounded-2xl rounded-tr-sm p-4 text-sm font-semibold shadow-lg shadow-brand-500/20 border border-brand-400/30">
                                                {res.question}
                                            </div>
                                        </div>

                                        {/* Assistant Response */}
                                        <div className="flex justify-start gap-3">
                                            <div className="w-8 h-8 rounded-full bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                                                <Bot className="w-5 h-5 text-brand-500" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <ResultCards result={res} isMinimal={true} />
                                                {res.was_self_corrected && (
                                                    <div className="mt-2 text-[10px] font-bold text-amber-500 uppercase tracking-widest flex items-center gap-1 px-1">
                                                        <Search className="w-3 h-3" /> Agent Reflexion Fix Applied
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Thinking Indicator */}
                        {isLoading && (
                            <div className="flex justify-start gap-3">
                                <div className="w-8 h-8 rounded-full bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                                    <Bot className="w-5 h-5 text-brand-500 animate-pulse" />
                                </div>
                                <div className="bg-slate-50 dark:bg-deep-800/40 rounded-2xl p-4 border border-slate-200 dark:border-deep-700">
                                    <div className="flex gap-1">
                                        <div className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <div className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <div className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* ── Input Area ────────────────────────────────────── */}
                    <div className="p-4 bg-white dark:bg-deep-900 border-t border-slate-200 dark:border-deep-800">
                        <QueryInterface
                            sessionId={sessionId}
                            profile={profile}
                            onResult={onResult}
                            onError={onError}
                            setIsLoading={setIsLoading}
                            setLoadingMessage={setLoadingMessage}
                            isLoading={isLoading}
                            isCompact={true}
                        />
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default ChatInterface;
