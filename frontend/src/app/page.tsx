"use client";

import React, { useState } from "react";
import { Provider } from "react-redux";
import store from "../store";
import LandingSection from "@/components/LandingSection";
import FileUploader from "@/components/FileUploader";
import ChatInterface from "@/components/ChatInterface";

const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleNextStep = () => setCurrentStep((prev) => prev + 1);
  const handleBackStep = () => setCurrentStep((prev) => prev - 1);

  return (
    <>
      {currentStep === 0 && <LandingSection onNext={handleNextStep} />}
      {currentStep === 1 && (
        <FileUploader
          onFileUpload={(file) => setUploadedFile(file)}
          onNext={handleNextStep}
          onBack={handleBackStep}
        />
      )}
      {currentStep === 2 && <ChatInterface onBack={handleBackStep} />}
    </>
  );
};

const Page: React.FC = () => {
  return (
    <Provider store={store}>
      <App />
    </Provider>
  );
};

export default Page;
