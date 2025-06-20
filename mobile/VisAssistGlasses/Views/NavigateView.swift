//
//  NavigateView.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/18/25.
//

import SwiftUI

struct NavigateView: View {
    var body: some View {
        VStack {
            Text("Navigate")
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.leading, 20)
                .font(.title)
                .fontWeight(.semibold)
                .foregroundStyle(.white)
            
            Spacer()
        }
    }
}

#Preview {
    NavigateView()
}
