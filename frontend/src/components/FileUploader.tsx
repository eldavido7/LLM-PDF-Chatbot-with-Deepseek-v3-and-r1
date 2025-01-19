import React, { useState } from "react";
import { motion } from "framer-motion";
import { Document, Page } from "react-pdf";
import { slideIn, fadeIn } from "../motion"; // Import from motion.js
import { uploadDocument } from "../app/api/chat.service"; // Import your service
import { toast, Toaster } from "sonner"; // Import Sonner for toast notifications
import { useDispatch } from "react-redux"; // Import Redux's useDispatch
import { pdfjs } from "react-pdf";
import { setSessionId } from "@/app/api/chat.slice";
import Loader from "../app/loader";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Set the worker externally - make sure this file exists in your public directory
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

interface FileUploaderProps {
  onFileUpload: (file: File) => void;
  onNext: () => void;
  onBack: () => void;
}

const FileUploader: React.FC<FileUploaderProps> = ({
  onFileUpload,
  onNext,
  onBack,
}) => {
  const dispatch = useDispatch();

  const [file, setFile] = useState<File | null>(null);
  const [pdfData, setPdfData] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false); // Track upload status

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const selectedFile = event.target.files[0];
      if (selectedFile.size > 1048576) {
        toast.error("File size exceeds 1MB. Please upload a smaller file.");
        return;
      }

      setFile(selectedFile);
      onFileUpload(selectedFile);

      // Read the file as a data URL to preview
      const reader = new FileReader();
      reader.onload = (e) => setPdfData(e.target?.result as string);
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error("No file selected. Please choose a file to upload.");
      return;
    }

    setIsUploading(true);
    setUploadComplete(false); // Reset upload status

    try {
      const { success, message, sessionId } = await uploadDocument(
        file,
        dispatch
      );

      if (success && sessionId) {
        toast.success(message || "File uploaded successfully!");
        dispatch(setSessionId(sessionId));
        setUploadComplete(true); // Mark upload as complete
      } else {
        throw new Error(message || "File upload failed.");
      }
    } catch (error: unknown) {
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("An unexpected error occurred during upload.");
      }
    } finally {
      setIsUploading(false); // Make sure this is called regardless of outcome
    }
  };

  return (
    <div className="h-screen flex flex-col items-center justify-center bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 text-white px-4">
      {/* Toast Container */}
      <Toaster position="top-right" toastOptions={{ duration: 3000 }} />

      {/* Back Button */}
      <button
        onClick={onBack}
        className="absolute top-6 left-6 px-4 py-2 bg-white text-indigo-600 font-bold rounded-full shadow-lg hover:bg-gray-200 transition"
      >
        Back
      </button>

      {/* File Upload Card */}
      <motion.div
        variants={slideIn("up", 0)}
        initial="initial"
        animate="animate"
        className="bg-white shadow-lg rounded-lg p-8 max-w-lg w-full"
      >
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">
          Upload Your PDF
        </h2>

        {/* File Input */}
        <div
          className={`border-2 ${
            file ? "border-blue-500" : "border-dashed border-gray-300"
          } rounded-lg p-6 text-center transition`}
        >
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
            id="fileInput"
          />
          <label
            htmlFor="fileInput"
            className="cursor-pointer text-gray-500 hover:text-gray-700 transition"
          >
            {file ? (
              <p className="text-gray-700 font-semibold">{file.name}</p>
            ) : (
              <p className="text-gray-500">
                Drag and drop your PDF here or click to browse
              </p>
            )}
          </label>
        </div>

        {/* PDF Preview */}
        {pdfData && (
          <motion.div
            variants={fadeIn("up", 0)}
            initial="initial"
            animate="animate"
            className="mt-6"
          >
            <h3 className="text-lg font-bold text-gray-800 mb-4">Preview</h3>
            <div className="border rounded-lg overflow-hidden">
              <Document file={pdfData} className="overflow-auto max-h-64">
                <Page pageNumber={1} scale={1.5} />
              </Document>
            </div>
          </motion.div>
        )}

        {/* Upload and Next Buttons */}
        <div className="flex justify-between items-center mt-6">
          <button
            className={`w-1/2 py-3 bg-green-500 text-white font-semibold rounded-lg shadow-md transition ${
              isUploading || uploadComplete ? "cursor-not-allowed" : ""
            }`}
            onClick={handleUpload}
            disabled={isUploading || uploadComplete}
          >
            {isUploading ? <Loader /> : "Upload"}
          </button>
          <button
            className={`w-1/2 ml-2 py-3 ${
              uploadComplete
                ? "bg-blue-500 text-white"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            } font-semibold rounded-lg shadow-md transition`}
            onClick={onNext}
            disabled={!uploadComplete}
          >
            Next
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default FileUploader;
