"use client";

import { motion } from "framer-motion";
import { Brain, Search, Book, Sparkles, Database, Newspaper } from "lucide-react";

export default function Home() {
    const features = [
        {
            title: "RAG Engine",
            description: "Autonomous document ingestion and semantic search.",
            icon: <Search className="w-6 h-6" />,
            status: "In Progress",
        },
        {
            title: "Topic Tracker",
            description: "Continuous monitoring of trends and updates.",
            icon: <Newspaper className="w-6 h-6" />,
            status: "Planned",
        },
        {
            title: "Knowledge Graph",
            description: "Mapping relationships between entities and concepts.",
            icon: <Database className="w-6 h-6" />,
            status: "Planned",
        },
    ];

    return (
        <main className="min-h-screen flex flex-col items-center justify-center p-6 md:p-24 relative overflow-hidden">
            {/* Hero Section */}
            <div className="z-10 text-center max-w-4xl space-y-8">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-sm font-medium text-primary mb-4"
                >
                    <Sparkles className="w-4 h-4" />
                    <span>Intelligent Research OS</span>
                </motion.div>

                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="text-6xl md:text-8xl font-bold tracking-tight bg-gradient-to-b from-white to-white/40 bg-clip-text text-transparent"
                >
                    Synapse
                </motion.h1>

                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.4 }}
                    className="text-lg md:text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto"
                >
                    Not a chatbot. A stateful intelligence engine that ingests, tracks, and scores decision-grade research in real-time.
                </motion.p>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.6 }}
                    className="flex flex-col sm:flex-row gap-4 justify-center"
                >
                    <button className="px-8 py-4 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 transition-all shadow-lg shadow-primary/20">
                        Launch Research Mode
                    </button>
                    <button className="px-8 py-4 glass text-white rounded-xl font-bold hover:bg-white/10 transition-all">
                        Explore Knowledge Base
                    </button>
                </motion.div>
            </div>

            {/* Feature Grid */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 0.8 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-32 w-full max-w-6xl z-10"
            >
                {features.map((feature, index) => (
                    <div
                        key={index}
                        className="p-8 rounded-2xl glass-dark hover:border-primary/50 transition-all group cursor-pointer"
                    >
                        <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
                            {feature.icon}
                        </div>
                        <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                        <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                            {feature.description}
                        </p>
                        <span className="text-[10px] uppercase tracking-widest text-primary font-bold opacity-60">
                            {feature.status}
                        </span>
                    </div>
                ))}
            </motion.div>

            {/* Decorative Elements */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] z-0 pointer-events-none opacity-20">
                <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_center,var(--color-primary)_0%,transparent_70%)] blur-[150px]" />
            </div>
        </main>
    );
}
