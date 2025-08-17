//
//  DashboardView.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/18/25.
//

import SwiftUI
import Speech
import AVFoundation

// Audio Player Delegate for handling completion
class AudioPlayerDelegate: NSObject, AVAudioPlayerDelegate {
    var onAudioFinished: (() -> Void)?
    
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        onAudioFinished?()
    }
}

struct DashboardView: View {
    let batteryPercentage = 65
    let paired = true
    private func speakResponse(_ text: String) {
        print("Speaking with ElevenLabs: \(text)")
        
        Task {
            do {
                let audioData = try await elevenLabsService.generateSpeech(text: text)
                
                // Configure audio session for playback
                let audioSession = AVAudioSession.sharedInstance()
                try audioSession.setCategory(.playback, mode: .default, options: [])
                try audioSession.setActive(true)
                
                // Set up delegate to restart background listening when audio finishes
                audioPlayerDelegate.onAudioFinished = {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                        self.startBackgroundListening()
                    }
                }
                
                // Create and play audio player with delegate
                audioPlayer = try AVAudioPlayer(data: audioData)
                audioPlayer?.delegate = audioPlayerDelegate
                audioPlayer?.prepareToPlay()
                audioPlayer?.play()
                
            } catch {
                print("ElevenLabs TTS Error: \(error)")
                // Fallback to native speech synthesis
                fallbackToNativeSpeech(text)
                
                // Restart background listening after fallback speech
                DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                    self.startBackgroundListening()
                }
            }
        }
    }
    
    private func fallbackToNativeSpeech(_ text: String) {
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        utterance.rate = 0.52
        speechSynthesizer.speak(utterance)
    }
    @StateObject private var apiViewModel = APIViewModel()
    @State private var isListening = false
    @State private var speechRecognizer = SFSpeechRecognizer()
    @State private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    @State private var recognitionTask: SFSpeechRecognitionTask?
    @State private var audioEngine = AVAudioEngine()
    @State private var speechSynthesizer = AVSpeechSynthesizer()
    @State private var silenceTimer: Timer?
    @State private var lastSpeechTime = Date()
    @State private var audioPlayer: AVAudioPlayer?
    
    // Add these new state variables with your existing @State variables
    @State private var isBackgroundListening = false
    @State private var backgroundRecognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    @State private var backgroundRecognitionTask: SFSpeechRecognitionTask?
    @State private var wakeWords = ["hey sight line", "hey site line", "hey sideline", "hay sight line", "hay site line", "hay sideline", "give me the power", "sight line", "site line", "sideline"]
    @State private var listeningMode: ListeningMode = .background
    @State private var audioPlayerDelegate = AudioPlayerDelegate()
    
    enum ListeningMode {
        case background  // Listening for wake words
        case active      // Listening for questions
    }
    
    private let elevenLabsService = ElevenLabsService.shared
    
    var body: some View {
        VStack {
            Text("Dashboard")
                .frame(maxWidth: .infinity, alignment: .leading)
                .font(.title)
                .fontWeight(.semibold)
                .foregroundStyle(.white)
            
            Image("glasses")
                .resizable()
                .scaledToFill()
                .frame(width: 300, height: 200)
                .clipped()
                .padding(.horizontal, 25)
                .padding(.bottom, 30)
                .background {
                    GeometryReader { geometry in
                        Path { path in
                            let width = geometry.size.width
                            let height = geometry.size.height
                            let cornerRadius = CGFloat(20)
                            let slantFactor = CGFloat(75)

                            path.move(to: CGPoint(x: width, y: height-slantFactor-cornerRadius))
                            path.addArc(center: CGPoint(x: width-cornerRadius, y: height-slantFactor + cornerRadius),
                                        radius: cornerRadius,
                                        startAngle: Angle(degrees: 0),
                                        endAngle: Angle(degrees: 90),
                                        clockwise: false)
                            
                            path.addLine(to: CGPoint(x: 0 + cornerRadius, y: height))
                            path.addArc(center: CGPoint(x: 0 + cornerRadius, y: height - cornerRadius),
                                        radius: cornerRadius,
                                        startAngle: Angle(degrees: 90),
                                        endAngle: Angle(degrees: 180),
                                        clockwise: false)
                            
                            path.addLine(to: CGPoint(x: 0, y: 0 + cornerRadius))
                            path.addArc(center: CGPoint(x: 0 + cornerRadius, y: 0 + cornerRadius),
                                        radius: cornerRadius,
                                        startAngle: Angle(degrees: 180),
                                        endAngle: Angle(degrees: 270),
                                        clockwise: false)
                            
                            path.addLine(to: CGPoint(x: width, y: 0))
                            path.addArc(center: CGPoint(x: width - cornerRadius, y: 0 + cornerRadius),
                                        radius: cornerRadius,
                                        startAngle: Angle(degrees: 270),
                                        endAngle: Angle(degrees: 0),
                                        clockwise: false)
                            
                            path.closeSubpath()
                        }
                        .stroke(
                            LinearGradient(
                                colors: [
                                    Color.init(hex: "#FFFFFF"),
                                    Color.init(hex: "#000000")],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing)
                                .opacity(0.95)
                        )
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color.init(hex: "#222834"),
                                    Color.init(hex: "#353F54")],
                                startPoint: .leading,
                                endPoint: .trailing)
                            .opacity(0.95)
                        )
                    }
                    .ignoresSafeArea()
                }
            
            cards
            
            Spacer()
        }
        .padding(.horizontal, 20)
        .background(ZStack {
            Color.init(hex: "#242C3B")
                .ignoresSafeArea()

            GeometryReader { geometry in
                Path { path in
                    let width = geometry.size.width
                    let height = geometry.size.height

                    path.move(to: CGPoint(x: width, y: height))
                    path.addLine(to: CGPoint(x: width, y: height - 650))
                    path.addLine(to: CGPoint(x: width - 135, y: height - 700))
                    path.addLine(to: CGPoint(x: width - 400, y: height))
                    path.closeSubpath()
                }
                .fill(LinearGradient(colors: [Color.init(hex: "#37B6E9"), Color.init(hex: "#4B4CED")], startPoint: .top, endPoint: .bottom))
            }
            .ignoresSafeArea()
        })
        .onChange(of: apiViewModel.response) { _, newResponse in
            if !newResponse.isEmpty {
                speakResponse(newResponse)
            }
        }
        .onAppear {
            startBackgroundListening()
        }
        .onDisappear {
            stopBackgroundListening()
        }
    }
    
    private func requestSpeechPermission() {
        SFSpeechRecognizer.requestAuthorization { status in
            DispatchQueue.main.async {
                switch status {
                case .authorized:
                    startListening()
                case .denied, .restricted, .notDetermined:
                    print("Speech recognition not authorized")
                @unknown default:
                    print("Unknown speech recognition status")
                }
            }
        }
    }
    
    private func startListening() {
        // Stop background listening first to avoid conflicts
        stopBackgroundListening()
        
        guard !audioEngine.isRunning else { return }
        
        // Cancel previous task
        recognitionTask?.cancel()
        recognitionTask = nil
        silenceTimer?.invalidate()
        
        // Configure audio session
        let audioSession = AVAudioSession.sharedInstance()
        try? audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
        try? audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        
        // Create recognition request
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else { return }
        recognitionRequest.shouldReportPartialResults = true
        
        isListening = true
        listeningMode = .active
        lastSpeechTime = Date()
        
        // Create recognition task
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { result, error in
            DispatchQueue.main.async {
                if let result = result {
                    // Reset silence timer when we get new speech
                    self.lastSpeechTime = Date()
                    self.silenceTimer?.invalidate()
                    
                    // Start a new silence timer
                    self.silenceTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: false) { _ in
                        // Stop listening after 2 seconds of silence
                        let finalText = result.bestTranscription.formattedString
                        if !finalText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                            self.processSpokenQuestion(finalText)
                        }
                        self.stopListening()
                    }
                }
                
                if error != nil {
                    self.stopListening()
                }
            }
        }
        
        // Configure audio input
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }
        
        audioEngine.prepare()
        try? audioEngine.start()
    }
    
    private func stopListening() {
        silenceTimer?.invalidate()
        silenceTimer = nil
        
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        
        recognitionTask?.cancel()
        recognitionTask = nil
        
        isListening = false
        listeningMode = .background
        
        // Don't restart background listening here - let speakResponse handle it
        // This prevents interrupting the ElevenLabs response
    }
    
    private func processSpokenQuestion(_ question: String) {
        // Clear previous response to ensure onChange triggers
        apiViewModel.response = ""
        apiViewModel.submitQuestion(question)
    }
    
//    private func speakResponse(_ text: String) {
//        print("test: \(text)")
//        
//        // Configure audio session for playback
//        let audioSession = AVAudioSession.sharedInstance()
//        do {
//            try audioSession.setCategory(.playback, mode: .default, options: [])
//            try audioSession.setActive(true)
//        } catch {
//            print("Failed to set audio session for playback: \(error)")
//        }
//        
//        let utterance = AVSpeechUtterance(string: text)
//        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
//        utterance.rate = 0.5
//        utterance.volume = 1.0
//        
//        speechSynthesizer.speak(utterance)
//    }
    
    var cards: some View {
        VStack {
            HStack {
                ZStack {
                    RoundedParallelogram(cornerRadius: 20, slantOffset: 8)
                        .stroke(
                            LinearGradient(
                                colors: [
                                    Color.init(hex: "#FFFFFF"),
                                    Color.init(hex: "#000000")],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing)
                            .opacity(0.95)
                        )
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color.init(hex: "#222834"),
                                    Color.init(hex: "#353F54")],
                                startPoint: .leading,
                                endPoint: .trailing)
                            .opacity(0.95)
                        )
                    
                    VStack {
                        BatteryCircle(percentage: CGFloat(batteryPercentage))
                            .padding(.top, 5)
                        
                        Text("Battery")
                            .font(.title3)
                            .fontWeight(.semibold)
                            .foregroundStyle(.white)
                            .padding(.top, 10)
                        
                        Text("\(batteryPercentage)%")
                            .foregroundStyle(.gray)
                    }
                    
                }
                .frame(height: 200)
                
                ZStack {
                    RoundedParallelogram(cornerRadius: 20, slantOffset: 8)
                        .stroke(
                            LinearGradient(
                                colors: [
                                    Color.init(hex: "#FFFFFF"),
                                    Color.init(hex: "#000000")],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing)
                            .opacity(0.95)
                        )
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color.init(hex: "#222834"),
                                    Color.init(hex: "#353F54")],
                                startPoint: .leading,
                                endPoint: .trailing)
                            .opacity(0.95)
                        )
                    
                    VStack {
                        Image(paired ? "paired" : "unpaired")
                            .resizable()
                            .scaledToFit()
                            .frame(width: 100)
                        
                        Text(paired ? "Connected" : "Disconnected")
                            .font(.title3)
                            .fontWeight(.semibold)
                            .foregroundStyle(.white)
                            .padding(.vertical, 10)
                    }
                }
                .frame(height: 200)
                .offset(y: -20)
            }
            
            HStack {
                ZStack {
                    RoundedParallelogramFlatBottom(cornerRadius: 20, slantOffset: 8)
                        .stroke(
                            LinearGradient(
                                colors: [
                                    Color.init(hex: "#FFFFFF"),
                                    Color.init(hex: "#000000")],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing)
                            .opacity(0.95)
                        )
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color.init(hex: "#222834"),
                                    Color.init(hex: "#353F54")],
                                startPoint: .leading,
                                endPoint: .trailing)
                            .opacity(0.95)
                        )
                    
                    VStack {
                        Button(action: {
                            if isListening {
                                stopListening()
                            } else {
                                requestSpeechPermission()
                            }
                        }) {
                            VStack {
                                Image(systemName: isListening ? "mic.fill" : "mic")
                                    .font(.system(size: 40))
                                    .foregroundColor(isListening ? .red : .white)
                                    .scaleEffect(isListening ? 1.2 : 1.0)
                                    .animation(.easeInOut(duration: 0.5).repeatForever(autoreverses: true), value: isListening)
                                
                                Text(isListening ? "Listening..." : "Ask Question")
                                    .font(.title3)
                                    .fontWeight(.semibold)
                                    .foregroundStyle(.white)
                                    .padding(.top, 10)
                                
                                if apiViewModel.isLoading {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                        .padding(.top, 5)
                                }
                            }
                        }
                        .disabled(apiViewModel.isLoading)
                    }
                    
                }
                .frame(height: 200)
            }
        }
    }
}

#Preview {
    DashboardView()
}

// MARK: - Background Listening for Wake Words
extension DashboardView {
    private func startBackgroundListening() {
        guard !audioEngine.isRunning else { return }
        
        SFSpeechRecognizer.requestAuthorization { status in
            DispatchQueue.main.async {
                guard status == .authorized else {
                    print("Speech recognition not authorized for background listening")
                    return
                }
                
                self.setupBackgroundListening()
            }
        }
    }
    
    private func setupBackgroundListening() {
        // Make sure we're not in active listening mode
        guard listeningMode == .background else { return }
        
        // Cancel previous background task
        backgroundRecognitionTask?.cancel()
        backgroundRecognitionTask = nil
        
        // Stop any active listening first
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
            recognitionTask?.cancel()
            recognitionTask = nil
        }
        
        // Configure audio session for background recording
        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            print("Failed to configure audio session for background listening: \(error)")
            return
        }
        
        // Create background recognition request
        backgroundRecognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let backgroundRecognitionRequest = backgroundRecognitionRequest else { return }
        backgroundRecognitionRequest.shouldReportPartialResults = true
        
        isBackgroundListening = true
        
        // Create background recognition task using the same speech recognizer
        backgroundRecognitionTask = speechRecognizer?.recognitionTask(with: backgroundRecognitionRequest) { result, error in
            DispatchQueue.main.async {
                // Only process if we're still in background mode
                guard self.listeningMode == .background else { return }
                
                if let result = result {
                    let spokenText = result.bestTranscription.formattedString.lowercased()
                    print(spokenText)
                    
                    // Check if any wake word was detected
                    for wakeWord in self.wakeWords {
                        if spokenText.contains(wakeWord.lowercased()) {
                            print("Wake word detected: \(wakeWord)")
                            self.handleWakeWordDetected()
                            break
                        }
                    }
                }
                
                if error != nil {
                    print("Background recognition error: \(error?.localizedDescription ?? "Unknown error")")
                    // Restart background listening after a short delay
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                        if self.listeningMode == .background {
                            self.startBackgroundListening()
                        }
                    }
                }
            }
        }
        
        // Configure audio input for background listening using the main audio engine
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            backgroundRecognitionRequest.append(buffer)
        }
        
        audioEngine.prepare()
        do {
            try audioEngine.start()
            print("Background listening started")
        } catch {
            print("Failed to start background audio engine: \(error)")
        }
    }
    
    private func stopBackgroundListening() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        
        backgroundRecognitionRequest?.endAudio()
        backgroundRecognitionRequest = nil
        
        backgroundRecognitionTask?.cancel()
        backgroundRecognitionTask = nil
        
        isBackgroundListening = false
        print("Background listening stopped")
    }
    
    private func handleWakeWordDetected() {
        // Stop background listening temporarily
        stopBackgroundListening()
        
        // Provide haptic feedback
        let notificationFeedback = UINotificationFeedbackGenerator()
        notificationFeedback.notificationOccurred(.success)
        
        self.startListening()
    }
}
