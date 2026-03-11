import { motion } from 'framer-motion';

const LoadingSpinner = ({ message }) => {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 dark:bg-deep-950/60 backdrop-blur-sm"
        >
            <div className="bg-white dark:bg-deep-900 p-8 rounded-3xl shadow-2xl flex flex-col items-center space-y-4 border border-slate-100 dark:border-deep-800 max-w-sm w-full mx-4">

                {/* Animated Bar Chart / Equalizer loader */}
                <div className="flex items-end justify-center h-16 space-x-2">
                    {[1, 0.6, 0.8, 0.4, 0.9].map((targetHeight, i) => (
                        <motion.div
                            key={i}
                            className="w-3 bg-brand-500 rounded-full"
                            initial={{ height: "30%" }}
                            animate={{ height: ["30%", `${targetHeight * 100}%`, "30%"] }}
                            transition={{
                                duration: 1.2,
                                repeat: Infinity,
                                ease: "easeInOut",
                                delay: i * 0.15
                            }}
                        />
                    ))}
                </div>

                <p className="text-lg font-medium text-slate-700 dark:text-slate-200 animate-pulse">
                    {message || 'Processing...'}
                </p>
                <div className="w-full text-center text-xs text-slate-400 dark:text-slate-500">
                    This might take a few seconds
                </div>
            </div>
        </motion.div>
    );
};

export default LoadingSpinner;
