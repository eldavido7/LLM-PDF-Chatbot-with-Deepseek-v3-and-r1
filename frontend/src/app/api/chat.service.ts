import axios from "axios";
import { AppDispatch } from "../../store";
import { setSessionId } from "./chat.slice";

// Define the base URL with proper type checking and fallback
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

// Validate BASE_URL at runtime
if (!BASE_URL) {
    console.error("BASE_URL is not defined in environment variables");
}

// Define response types for upload and chat
interface UploadResponse {
    message: string;
    session_id: string;
}

interface ChatResponse {
    answer: string;
}

// Function to get the full API URL
const getApiUrl = (endpoint: string): string => {
    const baseUrl = BASE_URL.endsWith('/') ? BASE_URL.slice(0, -1) : BASE_URL;
    const formattedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${baseUrl}${formattedEndpoint}`;
};

// Function to handle file upload
export const uploadDocument = async (
    file: File,
    dispatch: AppDispatch
): Promise<{ success: boolean; message: string; sessionId?: string }> => {
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await axios.post<UploadResponse>(getApiUrl('/upload'), formData, {
            headers: { "Content-Type": "multipart/form-data" },
        });

        if (response.status === 200) {
            const sessionId = response.data.session_id;
            dispatch(setSessionId(sessionId));

            return {
                success: true,
                message: response.data.message || "File uploaded successfully.",
                sessionId,
            };
        } else {
            throw new Error("Unexpected response from server");
        }
    } catch (error: unknown) {
        console.error('Upload error:', error);
        const errorMessage =
            (error instanceof Error && error.message) ||
            "Failed to upload file.";
        return { success: false, message: errorMessage };
    }
};

// Function to handle chat queries
export const sendChatQuery = async (
    question: string,
    sessionId: string,
    enableSummarization: boolean
): Promise<{ success: boolean; message: string }> => {
    try {
        const payload = {
            question,
            session_id: sessionId,
            enable_summarization: enableSummarization,
        };

        const response = await axios.post<ChatResponse>(getApiUrl('/chat'), payload, {
            headers: { "Content-Type": "application/json" },
        });

        let cleanedResponse = response.data.answer.trim();

        // Remove classification header if present (for greetings, irrelevant, etc.)
        if (cleanedResponse.includes("Classification:") && cleanedResponse.includes("Response:")) {
            cleanedResponse = cleanedResponse.split("Response:")[1]?.trim() || cleanedResponse;
        }
        // Remove "The user input is a relevant question related to the document." but keep everything after it
        else if (cleanedResponse.startsWith("The user input is a relevant question related to the document.")) {
            cleanedResponse = cleanedResponse.replace(
                "The user input is a relevant question related to the document.", ""
            ).trim();
        }
        else if (cleanedResponse.startsWith("The input is a relevant question related to the document.")) {
            cleanedResponse = cleanedResponse.replace(
                "The input is a relevant question related to the document.", ""
            ).trim();
        }
        else if (cleanedResponse.startsWith("The input is classified as a relevant question related to the document.")) {
            cleanedResponse = cleanedResponse.replace(
                "The input is classified as a relevant question related to the document.", ""
            ).trim();
        }

        // Remove <|end▁of▁sentence|> if present at the end
        cleanedResponse = cleanedResponse.replace(/<\|end▁of▁sentence\|>$/, "").trim();

        // Remove leading "?" if present
        cleanedResponse = cleanedResponse.replace(/^\?/, "").trim();

        // Remove asterisks for plain text display
        cleanedResponse = cleanedResponse.replace(/\*\*/g, "");

        return { success: true, message: cleanedResponse };
    } catch (error: unknown) {
        console.error('Chat error:', error);
        const errorMessage =
            (error instanceof Error && error.message) ||
            "Failed to send chat query.";
        return { success: false, message: errorMessage };
    }
};