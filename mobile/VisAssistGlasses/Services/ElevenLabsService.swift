//
//  ElevenLabsService.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/21/25.
//

import Foundation
import AVFoundation

struct ElevenLabsRequest: Codable {
    let text: String
    let model_id: String
    let voice_settings: VoiceSettings
    
    struct VoiceSettings: Codable {
        let stability: Double
        let similarity_boost: Double
        let style: Double
        let use_speaker_boost: Bool
    }
}

class ElevenLabsService {
    static let shared = ElevenLabsService()
    
    // Replace with your ElevenLabs API key
    private let apiKey = "sk_5c56dfc3be88f17f5045aceb686220f10217d506e4dbf68b"
    
    // Popular voice ID (Rachel - English, US)
    private let voiceId = "21m00Tcm4TlvDq8ikWAM"
    
    private let baseURL = "https://api.elevenlabs.io/v1"
    
    private init() {}
    
    func generateSpeech(text: String) async throws -> Data {
        guard let url = URL(string: "\(baseURL)/text-to-speech/\(voiceId)") else {
            throw ElevenLabsError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(apiKey, forHTTPHeaderField: "xi-api-key")
        request.timeoutInterval = 30.0
        
        let elevenLabsRequest = ElevenLabsRequest(
            text: text,
            model_id: "eleven_monolingual_v1",
            voice_settings: ElevenLabsRequest.VoiceSettings(
                stability: 0.5,
                similarity_boost: 0.5,
                style: 0.0,
                use_speaker_boost: true
            )
        )
        
        let jsonData = try JSONEncoder().encode(elevenLabsRequest)
        request.httpBody = jsonData
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw ElevenLabsError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw ElevenLabsError.serverError(httpResponse.statusCode)
        }
        
        return data
    }
    
    func playAudio(data: Data) throws {
        // Configure audio session for playback
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playback, mode: .default, options: [])
        try audioSession.setActive(true)
        
        // Create and play audio player
        let audioPlayer = try AVAudioPlayer(data: data)
        audioPlayer.prepareToPlay()
        audioPlayer.play()
    }
}

enum ElevenLabsError: Error {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case audioPlaybackError
    
    var localizedDescription: String {
        switch self {
        case .invalidURL:
            return "Invalid ElevenLabs URL"
        case .invalidResponse:
            return "Invalid response from ElevenLabs"
        case .serverError(let code):
            return "ElevenLabs server error: \(code)"
        case .audioPlaybackError:
            return "Audio playback error"
        }
    }
}
