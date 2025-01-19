import React from "react";
import { motion } from "framer-motion";
import { slideIn, fadeIn } from "../motion";
import Image from "next/image";

interface LandingSectionProps {
  onNext: () => void;
}

const LandingSection: React.FC<LandingSectionProps> = ({ onNext }) => {
  return (
    <div className="h-screen bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 text-white flex flex-col overflow-hidden">
      {/* Header */}
      <header className="w-full py-6 flex justify-between items-center max-w-6xl mx-auto px-2">
        {/* <div className="text-2xl font-bold tracking-wide">SmartPDF Chat</div> */}
      </header>

      {/* Main Content */}
      <div className="flex-grow flex items-center justify-center px-4">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          {/* Text Section */}
          <motion.div
            className="space-y-6 md:px-6"
            variants={fadeIn("up", 0)}
            initial="initial"
            animate="animate"
          >
            <motion.h1
              className="text-5xl md:text-6xl font-extrabold leading-tight text-center md:text-left"
              variants={fadeIn("up", 1)}
            >
              TL;DR <br /> Your PDFs in Seconds!
            </motion.h1>
            <motion.p
              className="text-lg leading-relaxed text-center md:text-left"
              variants={fadeIn("up", 2)}
            >
              Don&apos;t waste time reading lengthy documents. Upload your PDFs
              and get instant answers to your questions. It&apos;s fast, easy,
              and fun!
            </motion.p>
            <motion.div
              className="flex justify-center md:justify-start"
              variants={fadeIn("up", 3)}
            >
              <button
                onClick={onNext}
                className="px-8 py-4 bg-yellow-400 text-indigo-700 font-bold rounded-full shadow-lg hover:bg-yellow-300 transition"
              >
                Get Started
              </button>
            </motion.div>
          </motion.div>

          {/* Image Section */}
          <motion.div
            className="hidden md:flex justify-center items-center"
            variants={slideIn("right", 0)}
            initial="initial"
            animate="animate"
          >
            <div className="relative w-full max-w-md aspect-square">
              <Image
                src="/ai-chat-bot.png"
                alt="Chatbot Illustration"
                fill
                priority
                sizes="(min-width: 768px) 50vw, 100vw"
                className="object-contain"
              />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Footer */}
      <footer className="w-full py-4 text-center text-sm max-w-6xl mx-auto">
        &copy; {new Date().getFullYear()} SmartPDF Chat. All rights reserved.
      </footer>
    </div>
  );
};

export default LandingSection;
