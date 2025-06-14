//
//  ContentView.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/13/25.
//

import SwiftUI
import SwiftData

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        VStack {
            Image(systemName: "sunglasses.fill")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 100)
                .padding(.top, 15)
            
            Text("VisAssistGlasses")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Spacer()
        }
            
    }
}

#Preview {
    ContentView()
        //.modelContainer(for: Item.self, inMemory: true)
}
