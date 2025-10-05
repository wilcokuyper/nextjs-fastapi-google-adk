"use client";

import { PromptInput, PromptInputBody, PromptInputMessage, PromptInputSubmit, PromptInputTextarea, PromptInputToolbar, PromptInputTools } from "@/components/ai-elements/prompt-input";
import { useState } from "react";
import {useChat } from '@ai-sdk/react';
import { Conversation, ConversationContent, ConversationEmptyState, ConversationScrollButton } from "@/components/ai-elements/conversation";
import { MessageSquare } from "lucide-react";
import { Message, MessageContent } from "@/components/ai-elements/message";
import { Loader } from "@/components/ai-elements/loader";
import { Response } from '@/components/ai-elements/response';

export default function Page() {
    const [text, setText] = useState<string>('');

    const { messages, status, sendMessage } = useChat();

    const handleSubmit = (message: PromptInputMessage) => {
        if (!Boolean(message.text)) {
            return;
        }

        sendMessage({ text: message.text})
        setText('');
    }

    return (
        <div className="min-h-screen mx-auto max-w-4xl relative size-full">
            <div className="flex flex-col min-h-screen justify-between items-stretch size-full p-6">
            <Conversation className="grow">
                <ConversationContent>
                    {messages.length === 0 ? (
                        <ConversationEmptyState
                        icon={<MessageSquare className="size-12"/>}
                        title="No messages yet"
                        description="Start a conversation to see messages here"
                        />
                    ) : (
                        messages.map((message) => (
                            <Message from={message.role} key={message.id}>
                                <MessageContent>
                                {message.parts.map((part, i) => {
                                    switch (part.type) {
                                        case 'text':
                                            return (
                                                <Response key={`${message.id}-${i}`}>
                                                    {part.text}
                                                </Response>
                                            )
                                        };
                                    })
                                }
                                </MessageContent>
                            </Message>
                        ))
                    )}
                    {status === 'submitted' && <Loader />}
                </ConversationContent>
                <ConversationScrollButton/>
            </Conversation>
            <PromptInput onSubmit={handleSubmit} className="self-end">
                <PromptInputBody>
                    <PromptInputTextarea onChange={(e) => setText(e.target.value)} value={text}/>
                </PromptInputBody>
                <PromptInputToolbar>
                    <PromptInputTools>

                    </PromptInputTools>
                    <PromptInputSubmit
                        disabled={false}
                        status={'ready'}
                    />
                </PromptInputToolbar>
            </PromptInput>
            </div>
        </div>
    )
}