import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Plot from 'react-plotly.js';
import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import { vscDarkPlus, cb } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Code, Bot, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

SyntaxHighlighter.registerLanguage('python', python);

const Typewriter = ({ text }) => {
    const [displayedText, setDisplayedText] = useState("");
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        setDisplayedText("");
        setIsComplete(false);

        let i = 0;
        const speed = 30; // ms per character

        const timer = setInterval(() => {
            if (i < text.length) {
                setDisplayedText(text.substring(0, i + 1));
                i++;
            } else {
                setIsComplete(true);
                clearInterval(timer);
            }
        }, speed);

        return () => clearInterval(timer);
    }, [text]);

    return (
        <span className="relative inline">
            {displayedText}
            {!isComplete && (
                <motion.span
                    initial={{ opacity: 1 }}
                    className="inline-flex items-center ml-1.5 text-brand-500"
                    style={{ verticalAlign: 'middle', marginTop: '-0.1em' }}
                >
                    <Bot className="w-[1.1em] h-[1.1em]" />
                </motion.span>
            )}
        </span>
    );
};

const ResultCards = ({ result, isMinimal = false }) => {
    const [showCode, setShowCode] = useState(false);

    // Fallback styling if frontend theme detection needs it
    const isDark = document.documentElement.classList.contains('dark');
    const codeStyle = isDark ? vscDarkPlus : cb;

    return (
        <motion.div
            initial={isMinimal ? { opacity: 0, x: -20 } : { opacity: 0, y: 30 }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.4, type: 'spring', bounce: 0.3 }}
            className={`${isMinimal ? 'bg-white dark:bg-deep-900/90 rounded-2xl rounded-tl-none border border-slate-200 dark:border-deep-800 p-4 w-full shadow-md' : 'bg-white dark:bg-deep-900 rounded-3xl overflow-hidden shadow-lg border border-slate-200 dark:border-deep-800 glass-panel dark:glass-dark'}`}
        >
            {/* Header - The Question (Hidden in minimal mode) */}
            {!isMinimal && (
                <div className="px-6 py-4 bg-slate-50 dark:bg-deep-800/40 border-b border-slate-100 dark:border-deep-800 flex items-start space-x-3">
                    <HelpCircle className="w-6 h-6 text-brand-500 mt-0.5 flex-shrink-0" />
                    <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-100">
                        {result.question}
                    </h3>
                </div>
            )}
            {/* Main Content - Chart or Text Result */}
            <div className={isMinimal ? "space-y-4" : "p-6"}>
                {/* Result (Chart or Raw Data) */}
                {result.chart_json ? (
                    <div className={`w-full bg-white dark:bg-deep-950/40 rounded-xl overflow-hidden border border-slate-200 dark:border-deep-800 flex justify-center ${isMinimal ? 'shadow-sm' : 'mb-6 shadow-inner'}`}>
                        <Plot
                            data={result.chart_json.data}
                            layout={{
                                ...result.chart_json.layout,
                                autosize: true,
                                paper_bgcolor: 'transparent',
                                plot_bgcolor: 'transparent',
                                font: {
                                    family: 'Inter, system-ui, sans-serif',
                                    color: isDark ? '#f1f5f9' : '#1e293b'
                                },
                                margin: isMinimal ? { t: 10, r: 10, b: 30, l: 30 } : { t: 40, r: 20, b: 40, l: 40 },
                                height: isMinimal ? 280 : undefined
                            }}
                            useResizeHandler={true}
                            style={{ width: '100%', minHeight: isMinimal ? '280px' : '400px' }}
                            config={{ displayModeBar: !isMinimal, responsive: true }}
                        />
                    </div>
                ) : (
                    <div className={`bg-slate-50 dark:bg-deep-800/40 rounded-xl text-center border border-slate-200 dark:border-deep-800 ${isMinimal ? 'p-4' : 'p-8 mb-6'}`}>
                        <p className={`${isMinimal ? 'text-lg' : 'text-2xl'} font-semibold font-mono text-slate-800 dark:text-slate-200`}>
                            {result.raw_result || "No visualizable data returned."}
                        </p>
                    </div>
                )}

                {/* AI Insight Box - Back to the Bottom */}
                {result.insight && (
                    <div className={`${isMinimal ? 'p-3 rounded-xl bg-brand-50 dark:bg-brand-900/10 border border-brand-100 dark:border-brand-500/20' : 'bg-gradient-to-r from-brand-50 to-fuchsia-50 dark:from-brand-900/10 dark:to-fuchsia-900/10 border border-brand-100 dark:border-brand-500/20 rounded-2xl p-6 shadow-sm'} relative overflow-hidden flex items-start space-x-3`}>
                        {!isMinimal && <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/5 blur-3xl rounded-full"></div>}
                        <Bot className={`${isMinimal ? 'w-5 h-5' : 'w-8 h-8'} text-brand-600 dark:text-brand-400 mt-0.5 flex-shrink-0`} />
                        <div>
                            <h4 className={`${isMinimal ? 'text-[10px] font-bold uppercase tracking-wider' : 'font-semibold mb-1'} text-brand-800 dark:text-brand-400 opacity-80`}>
                                AI Analyst Insight
                            </h4>
                            <p className={`text-slate-700 dark:text-slate-300 leading-relaxed ${isMinimal ? 'text-sm' : 'text-lg'}`}>
                                <Typewriter text={result.insight} />
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* Collapsible Code Section (Only in Full mode or hidden in Minimal) */}
            {!isMinimal && (
                <div className="border-t border-slate-100 dark:border-deep-800">
                    <button
                        onClick={() => setShowCode(!showCode)}
                        className="w-full px-6 py-4 flex items-center justify-between text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-deep-800/40 transition-colors"
                    >
                        <span className="flex items-center">
                            <Code className="w-4 h-4 mr-2" />
                            View Generated Pandas Code
                        </span>
                        {showCode ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>

                    <AnimatePresence>
                        {showCode && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.3 }}
                                className="overflow-hidden"
                            >
                                <div className="p-4 bg-slate-950">
                                    <SyntaxHighlighter
                                        language="python"
                                        style={codeStyle}
                                        customStyle={{ margin: 0, padding: '1rem', background: 'transparent', fontSize: '0.9rem' }}
                                    >
                                        {result.generated_code}
                                    </SyntaxHighlighter>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            )}
        </motion.div>
    );
};

export default ResultCards;
