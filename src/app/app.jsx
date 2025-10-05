"use client";
import { unstable_ViewTransition as ViewTransition } from 'react';
import { startTransition, useState } from "react";

export default function App() {
    const [large, setLarge] = useState(false);

    return (
        <div className="min-h-screen flex justify-center items-center">
            {large ? (
        <ViewTransition name="boxes">
        <div className="bg-red-600 text-white p-5" onClick={() => startTransition(() => setLarge(false))}>Large</div>
        </ViewTransition>
    ) : (
            <ViewTransition name="boxes">
        <div className="bg-blue-700 text-white p-10" onClick={() => startTransition(() => setLarge(true))}>Small</div>
        </ViewTransition> 
     )
    }</div>
    )
}