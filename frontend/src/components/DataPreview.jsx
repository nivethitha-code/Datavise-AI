const DataPreview = ({ profile, previewData }) => {
    if (!profile || !previewData) return null;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* File Info Header */}
            <div className="flex items-center justify-between glass-panel dark:glass-dark p-6 rounded-2xl bg-white dark:bg-deep-900 shadow-sm border border-slate-200 dark:border-deep-800">
                <div>
                    <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">Dataset Loaded</h2>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">
                        <span className="font-mono bg-slate-100 dark:bg-deep-800 px-2 py-0.5 rounded text-sm text-brand-600 dark:text-brand-400 font-medium">{profile.filename}</span>
                        <span className="mx-2 text-slate-300 dark:text-deep-800">•</span>
                        <span>{profile.rows.toLocaleString()} rows</span>
                        <span className="mx-2 text-slate-300 dark:text-deep-800">•</span>
                        <span>{profile.columns.length} columns</span>
                    </p>
                </div>
                <div className="hidden sm:block">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                        Ready for AI Analysis
                    </span>
                </div>
            </div>

            {/* Statistics Cards - Horizontal Scroll */}
            <div className="relative">
                <div className="flex space-x-4 overflow-x-auto pb-4 pt-2 px-1 snap-x scrollbar-hide">
                    {profile.columns.map((col, idx) => (
                        <div
                            key={idx}
                            className="flex-shrink-0 w-64 glass-panel dark:glass-dark bg-white dark:bg-deep-900 p-5 rounded-2xl shadow-sm border border-slate-200 dark:border-deep-800 snap-start hover:border-brand-300 dark:hover:border-brand-500/50 transition-colors"
                        >
                            <div className="flex justify-between items-start mb-3">
                                <h3 className="font-semibold text-slate-800 dark:text-slate-200 truncate pr-2" title={col.name}>
                                    {col.name}
                                </h3>
                                <span className={`text-xs px-2 py-1 rounded-md font-medium capitalize
                  ${col.type === 'numeric' ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400' :
                                        col.type === 'datetime' ? 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-400' :
                                            'bg-slate-100 text-slate-700 dark:bg-deep-800 dark:text-slate-300'}`}
                                >
                                    {col.type}
                                </span>
                            </div>

                            <div className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
                                <div className="flex justify-between">
                                    <span>Unique:</span>
                                    <span className="font-mono">{col.unique_count.toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Missing:</span>
                                    <span className="font-mono">{col.null_count.toLocaleString()}</span>
                                </div>

                                {col.type === 'numeric' && col.mean !== undefined && (
                                    <div className="pt-2 mt-2 border-t border-slate-100 dark:border-slate-700/50 flex justify-between">
                                        <span>Avg:</span>
                                        <span className="font-mono font-medium text-slate-800 dark:text-slate-300">
                                            {typeof col.mean === 'number' ? (Number.isInteger(col.mean) ? col.mean : col.mean.toFixed(2)) : col.mean}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Data Preview Table */}
            <div className="glass-panel dark:glass-dark bg-white dark:bg-deep-950 rounded-3xl shadow-sm border border-slate-200 dark:border-deep-800 overflow-hidden">
                <div className="border-b border-slate-200 dark:border-deep-800 px-6 py-4 flex justify-between items-center bg-slate-50 dark:bg-deep-900/50">
                    <h3 className="font-semibold text-slate-700 dark:text-slate-300">Data Preview (First 10 Rows)</h3>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-slate-500 dark:text-slate-400 uppercase bg-slate-50 dark:bg-deep-800/50">
                            <tr>
                                {profile.columns.map((col, idx) => (
                                    <th key={idx} className="px-6 py-3 font-medium tracking-wider whitespace-nowrap">
                                        {col.name}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-deep-800">
                            {previewData.map((row, rowIdx) => (
                                <tr key={rowIdx} className="hover:bg-slate-50 dark:hover:bg-brand-500/5 transition-colors">
                                    {profile.columns.map((col, colIdx) => (
                                        <td key={colIdx} className={`px-6 py-3 whitespace-nowrap text-slate-600 dark:text-slate-300 ${col.type === 'numeric' ? 'font-mono text-right text-brand-600 dark:text-brand-400' : ''}`}>
                                            {row[col.name] !== null ? String(row[col.name]) : <span className="text-slate-300 dark:text-deep-800 italic">null</span>}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default DataPreview;