//
//  APIService.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/21/25.
//

import Foundation

struct QuestionRequest: Codable {
    let question: String
}

struct QuestionResponse: Codable {
    let response: String
}

class APIService {
    static let shared = APIService()
    private let baseURL = "http://192.168.7.49:8080"
    
    private init() {}
    
    func submitQuestion(_ question: String) async throws -> QuestionResponse {
        guard let url = URL(string: "\(baseURL)/question") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 10.0
        
        let questionRequest = QuestionRequest(question: question)
        let jsonData = try JSONEncoder().encode(questionRequest)
        request.httpBody = jsonData
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.serverError
        }
        
        let questionResponse = try JSONDecoder().decode(QuestionResponse.self, from: data)
        return questionResponse
    }
}

enum APIError: Error {
    case invalidURL
    case serverError
    case decodingError
}
