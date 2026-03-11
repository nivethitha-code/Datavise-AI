import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileSpreadsheet } from 'lucide-react';
import axios from 'axios';

const FileUpload = ({ onSuccess, onError, setIsLoading, setLoadingMessage }) => {
    const onDrop = useCallback(async (acceptedFiles) => {
        const file = acceptedFiles[0];
        if (!file) return;

        if (!file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
            onError("Please upload a .csv or .xlsx file.");
            return;
        }

        setIsLoading(true);
        setLoadingMessage("Reading and profiling your data...");

        const formData = new FormData();
        formData.append('file', file);

        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await axios.post(`${apiUrl}/api/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            onSuccess(response.data);
        } catch (err) {
            if (err.response && err.response.data && err.response.data.detail) {
                onError(err.response.data.detail);
            } else {
                onError("Failed to upload the file. Please check your connection and try again.");
            }
        } finally {
            setIsLoading(false);
        }
    }, [onSuccess, onError, setIsLoading, setLoadingMessage]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
        },
        maxFiles: 1
    });

    return (
        <div className="w-full max-w-3xl mx-auto mt-12">
            <div
                {...getRootProps()}
                className={`relative group cursor-pointer flex flex-col items-center justify-center p-16 text-center border-2 border-dashed rounded-3xl transition-all duration-300
          ${isDragActive
                        ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/20'
                        : 'border-slate-300 dark:border-deep-800 hover:border-brand-400 hover:bg-slate-50 dark:hover:bg-deep-900/50 glass-panel dark:glass-dark'
                    }`}
            >
                <input {...getInputProps()} />

                {/* Glow effect behind icon */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
                    <div className="w-32 h-32 bg-brand-400/20 dark:bg-brand-500/10 blur-3xl rounded-full"></div>
                </div>

                <div className="relative bg-white dark:bg-deep-900 p-4 rounded-2xl shadow-sm border border-slate-100 dark:border-deep-800 mb-6 group-hover:scale-110 transition-transform duration-300">
                    {isDragActive ? (
                        <UploadCloud className="w-10 h-10 text-brand-500" />
                    ) : (
                        <FileSpreadsheet className="w-10 h-10 text-slate-400 group-hover:text-brand-500 transition-colors" />
                    )}
                </div>

                <h3 className="text-2xl font-semibold mb-2 text-slate-700 dark:text-slate-200">
                    {isDragActive ? 'Drop your data here' : 'Select a CSV or Excel file'}
                </h3>

                <p className="text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
                    Drag and drop your spreadsheet here, or click to browse. We'll automatically profile and prepare it for AI analysis.
                </p>
            </div>

            {/* Feature callouts placeholder below upload */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 text-center text-slate-500 dark:text-slate-400">
                <div className="glass-panel dark:glass-dark p-6 rounded-2xl shadow-sm">
                    <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1">Instant Insights</h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Ask questions in plain English and get answers instantly.</p>
                </div>
                <div className="glass-panel dark:glass-dark p-6 rounded-2xl shadow-sm">
                    <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1">Auto-Charts</h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Every answer comes with a fully interactive Plotly visualization.</p>
                </div>
                <div className="glass-panel dark:glass-dark p-6 rounded-2xl shadow-sm">
                    <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-1">Code Transparency</h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400">See the exact Python Pandas code generated under the hood.</p>
                </div>
            </div>
        </div>
    );
};

export default FileUpload;
