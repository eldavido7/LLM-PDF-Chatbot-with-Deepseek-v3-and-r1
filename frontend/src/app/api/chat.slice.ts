import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface Message {
    type: "question" | "answer";
    text: string;
}

interface ChatState {
    messages: Message[];
    sessionId: string | null;
    isLoading: boolean;
    error: string | null;
}

const initialState: ChatState = {
    messages: [],
    sessionId: null,
    isLoading: false,
    error: null,
};

const chatSlice = createSlice({
    name: "chat",
    initialState,
    reducers: {
        setSessionId(state, action: PayloadAction<string>) {
            state.sessionId = action.payload;
        },
        addMessage(state, action: PayloadAction<Message>) {
            state.messages.push(action.payload);
        },
        setLoading(state, action: PayloadAction<boolean>) {
            state.isLoading = action.payload;
        },
        setError(state, action: PayloadAction<string | null>) {
            state.error = action.payload;
        },
        clearChat(state) {
            state.messages = [];
            state.sessionId = null;
            state.isLoading = false;
            state.error = null;
        },
    },
});

export const { setSessionId, addMessage, setLoading, setError, clearChat } = chatSlice.actions;

export default chatSlice.reducer;
