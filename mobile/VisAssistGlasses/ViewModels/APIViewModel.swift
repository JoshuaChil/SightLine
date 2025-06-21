//
//  APIViewModel.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/21/25.
//

import Foundation

@MainActor
class APIViewModel: ObservableObject {
    @Published var response: String = ""
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    
    private let apiService = APIService.shared
    
    func submitQuestion(_ question: String) {
        Task {
            isLoading = true
            errorMessage = nil
            
            do {
                let result = try await apiService.submitQuestion(question)
                response = result.response
            } catch {
                errorMessage = "Failed to submit question: \(error.localizedDescription)"
            }
            
            isLoading = false
        }
    }
}